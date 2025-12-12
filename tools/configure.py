#!/usr/bin/env python3

#
# Neovim LSP config for this file, because I indent in my own style:
#
# local py_conf = { pylsp = { plugins = { pycodestyle = {
#   enabled       = true,
#   ignore        = { "E251", "E221" },
#   maxLineLength = 100,
# } } } }
# vim.lsp.config("pylsp", { settings = py_conf })
#

import json
import os
from   pathlib     import Path
import argparse
import sys
import subprocess
from   dataclasses import dataclass
from   typing      import Any, Tuple

import ninja_syntax


#   ############# ^^         IMPORTS         ^^ #############
#   ##############                             ##############
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   ##############                             ##############
#   ############# vv CONSTANTS/PROJECT INPUT vv #############


ROOT_PATH = Path(".")

NINJA_FILE    = ROOT_PATH / "build.ninja"

EXTRACT_DIR   = ROOT_PATH / "extract"
BUILD_DIR     = ROOT_PATH / "build"
CONF_DIR      = ROOT_PATH / "dsd-config"
SRC_DIR       = ROOT_PATH / "src"                # game
INC_DIR       = ROOT_PATH / "include"            # headers
LIBS_DIR      = ROOT_PATH / "libs"               # libraries used
LIBS_INC_DIR  = ROOT_PATH / "libs" / "include"   # library headers

ROM_FILE      = ROOT_PATH / "rom" / "atc.nds"
OUT_FILE      = ROOT_PATH / "rom" / "out.nds"    # The output ROM
OUT_SHA1_FILE = ROOT_PATH / "rom" / "out.sha1"   # The output ROM
BIOS_FILE     = ROOT_PATH / "rom" / "bios7.bin"  # optional (not really)

DSD           = ROOT_PATH / "tools" / "dsd"
OBJDIFF       = ROOT_PATH / "tools" / "objdiff"
OBJDIFF_CLI   = ROOT_PATH / "tools" / "objdiff-cli"
SHA1          = ROOT_PATH / "tools" / "sha1.py"
WIBO          = ROOT_PATH / "tools" / "wibo"

MWCC_DIR      = ROOT_PATH / "tools" / "mwccarm"

DECOMP_ME_COMPILER = "mwcc_30_131"


# Derivative values:
DELINKS_DIR   = BUILD_DIR / "delinks"



@dataclass(frozen=True)
class CompilerConfig:
    version: str
    flags: Tuple[str, ...]

    def compiler_bin(self):
        return os.path.join(".", MWCC_DIR / self.version / "mwccarm.exe")

    def linker_bin(self):
        return os.path.join(".", MWCC_DIR / self.version / "mwldarm.exe")


# Used when source not found in PER_SOURCE_COMPILER_CONFIGS.
DEFAULT_COMPILER_CONFIG = CompilerConfig(
    version = "2.0/sp1p5",
    flags   = (
        # Leave this as first arg! (maybe?)
        "-O4,p",           # Optimization lvl 4, speed

        "-enum int",       # Use int-sized enums
        "-char signed",    # Char type is signed
        "-proc arm946e",   # Target processor
        "-gccext,on",      # Enable GCC extensions
        "-fp soft",        # Compute float operations in software
        "-inline noauto",  # Inline only functions marked with 'inline'

        # FIX: Add string reuse and exception flags
        "-str noreuse",    # Repeats the same string in the binary

        "-RTTI off",       # Disable runtime type information
        "-interworking",   # Enable ARM/Thumb interworking
        "-w off",          # Disable warnings
        "-sym on",         # Debug info, including line numbers
        "-gccinc",         # Interpret #include "..." and <...> equally
        "-msgstyle gcc",   # Use GCC-like messages (helsp some IDEs)
        "-enc SJIS",       # Use Shift-JIS encoding
        "-nolink",         # Do not link

        "-ipa file"        # Interprocedural analysis level: file

        # Language flag added in compiler_config_for_source()
        # "-lang=xxx",       # c/c++/ec/c99 - passed to linker
    )
)

PER_SOURCE_COMPILER_CONFIGS: dict[Path, CompilerConfig] = {
    Path(SRC_DIR / "some_dir" / "some_file.c"): CompilerConfig(
        version = "1.2/sp4",
        flags     = (
            "-O3,p",
            "-gccinc",
            "-enc SJIS",
            # other flags goes here...
        )
    )
}


def compiler_config_for_source(source_file: Path) -> CompilerConfig:
    def to_repo_relative(p: Path) -> Path:
        try:
            return p.relative_to(ROOT_PATH)
        except ValueError:
            try:
                return p.relative_to(ROOT_PATH.resolve())
            except ValueError:
                return p
    rel_p = to_repo_relative(source_file)
    flags = PER_SOURCE_COMPILER_CONFIGS.get(rel_p, DEFAULT_COMPILER_CONFIG)

    lang_flag = ""
    if is_c(rel_p):
        lang_flag = "-lang=c99"
    if is_cpp(rel_p):
        lang_flag = "-lang=c++"

    return flags + (lang_flag,)


# Passed to all modules and final arm9.o link
LD_FLAGS = " ".join(
    [
        "-proc arm946e",        # Target processor
        "-interworking",        # Enable ARM/Thumb interworking
        "-map closure,unused",  # Generate map file
        "-msgstyle gcc",        # Use GCC-like messages (helps some IDEs)
        "-nodead",              # Do not strip unused code
        "-nostdlib",            # Do not link to MWLibraries
    ]
)

# Only passed to the module links. Link as a static library.
MODULE_LD_FLAGS = " ".join(["-library"])

# Only passed to the final arm9.o link. Sets entry function.
ARM9_LD_FLAGS = " ".join(["-m Entry"])

# This is for decomp.me
DSD_OBJDIFF_ARGS = " ".join(
    [
        "--scratch",
        f"--compiler {DECOMP_ME_COMPILER}",
        f'--c-flags "{DEFAULT_COMPILER_CONFIG.flags}"',
        # Command for rebuilding files:
        "--custom-make ninja",
    ]
)

DSD_BASE_FLAGS = " ".join(["--force-color"])

# for more advance stuff, see TWEWY code
CC_INCLUDES = " ".join([f"-i {INC_DIR}", f"-i {LIBS_INC_DIR}"])


#   ############# ^^ CONSTANTS/PROJECT INPUT ^^ #############
#   ##############                             ##############
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   ##############                             ##############
#   ############# vv PROJECT CLASS + HELPERS vv #############


# p = Project(args.version, platform=platform, delinks_json=delinks_json)
class Project:
    def __init__(self, delinks_json: Any | None):

        self.delinks_json = delinks_json  # delinks JSON data from dsd

        self.game_config  = CONF_DIR
        self.game_build   = BUILD_DIR
        self.game_extract = EXTRACT_DIR

        def get_config_files(name: str) -> list[str]:
            return [
                f"{root}/{file}"
                for root, _, files in os.walk(CONF_DIR)
                for file in files
                if file == name
            ]

        self.delinks_files = get_config_files("delinks.txt")
        self.relocs_files  = get_config_files("relocs.txt")
        self.symbols_files = get_config_files("symbols.txt")


    def dsd_configs(self) -> list[str]:
        return self.delinks_files + self.relocs_files + self.symbols_files

    def arm9_config_yaml(self) -> Path:
        return self.game_config / "arm9" / "config.yaml"

    def baserom(self) -> Path:
        return ROM_FILE

    def build_rom(self) -> Path:
        return OUT_FILE

    def baserom_config(self) -> Path:
        return self.game_extract / "config.yaml"

    def build_rom_config(self) -> Path:
        return self.game_build / "build" / "rom_config.yaml"

    def source_object_files(self) -> list[str]:
        files: list[str] = []
        for src_path in get_c_cpp_files([SRC_DIR, LIBS_DIR]):
            src_obj_path = self.game_build / src_path
            files.append(str(src_obj_path.with_suffix(".o")))
        return files

    def arm9_o(self) -> Path:
        return self.game_build / "arm9.o"

    def arm9_disassembly_dir(self) -> Path:
        return self.game_build / "asm"

    def objdiff_report(self) -> Path:
        return self.game_build / "report.json"

    def files(self) -> list[dict[str, str]]:
        return self.delinks_json["files"]

    def delink_files(self) -> list[str]:
        delink_files = [file["delink_file"] for file in self.files()]
        return list(set(delink_files))

    def arm9_lcf_file(self) -> str:
        return self.delinks_json["arm9_lcf_file"]

    def arm9_objects_file(self) -> str:
        return self.delinks_json["arm9_objects_file"]

    def rom_sha1_file(self) -> str:
        return OUT_SHA1_FILE


def get_c_cpp_files(dirs: list[Path]):
    for dir in dirs:
        for root, _, files in os.walk(dir):
            root = Path(root)
            for file in files:
                if is_cpp(file) or is_c(file):
                    yield root / file


def is_cpp(name: str | Path):
    return Path(name).suffix in [".cpp"]


def is_c(name: str | Path):
    return Path(name).suffix in [".c"]


#   ############# ^^ PROJECT CLASS + HELPERS ^^ #############
#   ##############                             ##############
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   #########################################################
#   ##############                             ##############
#   ############# vv      MAIN FUNCTION      vv #############


# Small helper function.
def leave(*strs):
    for s in strs:
        print(s)
    exit(1)


def main():
    if Path.cwd().name != "atc":
        leave(
            "Not runnig from project root directory!",
            "Stand in project root and run like this:",
            "\t$ ./tools/configure.py",
            "Exiting...")
    if not MWCC_DIR.is_dir():
        leave(
            f"Could not locate MWCC directory: {MWCC_DIR}",
            "Run this to download the compiler collection:",
            "\t$ tools/get_mwccarm.sh")
    if not DSD.exists():
        leave(f"Could not find program: {DSD}")

    json_cmd = [
        DSD, DSD_BASE_FLAGS, "json", "delinks",
        "--config-path", f"{CONF_DIR / 'arm9' / 'config.yaml'}"]
    out = subprocess.run(json_cmd, capture_output=True, text=True)
    if out.returncode != 0:
        json_cmd[0] = str(json_cmd[0])  # Can't call join without this.
        leave(
            "Error running command:",
            f"\t{" ".join(json_cmd)}",
            "Failed with:"
            f"{out.stderr.strip()}")

    delinks_json = json.loads(out.stdout)
    # print( json.dumps(delinks_json,indent=2) )

    file = None
    try:
        file = NINJA_FILE.open("w")
    except OSError as e:
        leave(
            f"Could not open {NINJA_FILE} for writing. Error was:",
            f"\t{e}"
        )


    # ############# ERROR CHECKING ############# #
    ##############################################
    ##############################################
    # ############ NINJA CODE START ############ #


    n = ninja_syntax.Writer(file)
    p = Project(delinks_json=delinks_json)


    n.comment("Arm7 bios file is optional, but highly recomended.")
    if BIOS_FILE.is_file():
        n.variable("arm7_bios_flag", f"--arm7-bios {BIOS_FILE}")
    else:
        n.variable("arm7_bios_flag", "")
    n.newline()


    # ############ NINJA CODE START ############ #
    ##############################################
    ##############################################
    # ############ DSD ROM COMMANDS ############ #

    n.comment(f"Extract the rom content into dir {EXTRACT_DIR}")
    n.rule(
        name    = "rom_extract",
        command = f"{DSD} {DSD_BASE_FLAGS} rom extract "
                  "--output-path $output_path "
                  "--rom $in "
                  "$arm7_bios_flag")
    n.build(
        inputs    = str(ROM_FILE),
        rule      = "rom_extract",
        outputs   = str(p.baserom_config()),  # extract/config.yaml
        variables = {"output_path": str(EXTRACT_DIR)})
    n.newline()


    n.comment(f"Create a rom building config: {p.build_rom_config()}")
    n.rule(
        name    = "rom_config",
        command = f"{DSD} {DSD_BASE_FLAGS} rom config "
                  "--elf $in "
                  "--config $config_path")
    n.build(
        inputs    = str(p.arm9_o()),
        rule      = "rom_config",
        outputs   = str(p.build_rom_config()),
        variables = {"config_path": str(p.arm9_config_yaml())})
    n.newline()


    n.comment(f"Build the output rom: {OUT_FILE}")
    n.rule(
        name    = "rom_build",
        command = f"{DSD} {DSD_BASE_FLAGS} rom build "
                  "--config $in "
                  "--rom $out "
                  "$arm7_bios_flag")
    n.build(
        inputs  = str(p.build_rom_config()),
        rule    = "rom_build",
        outputs = str(p.build_rom()))
    n.newline()


    # ############ DSD ROM COMMANDS ############ #
    ##############################################
    ##############################################
    # ############ LINKER PREPARING ############ #


    n.comment(f"Create delinked .o files in {DELINKS_DIR}")
    n.rule(
        name    = "delink",
        command = f"{DSD} {DSD_BASE_FLAGS} delink "
                  "--config-path $config_path")
    n.build(
        inputs    = p.dsd_configs() + [str(p.baserom_config())],
        rule      = "delink",
        outputs   = p.delink_files(),
        variables = {"config_path": str(p.arm9_config_yaml())})
    n.newline()


    n.comment(f"Use dsd to create linking file: {p.arm9_lcf_file()}")
    n.rule(
        name    = "lcf",
        command = f"{DSD} {DSD_BASE_FLAGS} lcf "
                  "--config-path $config_path")
    n.build(
        inputs    = p.delinks_files + [str(p.baserom_config())],
        rule      = "lcf",
        outputs   = [p.arm9_lcf_file(), p.arm9_objects_file()],
        variables = {
            "config_path": str(p.arm9_config_yaml())})
    n.newline()


    n.comment("Probably won't be used, but is here for completeness.")
    n.rule(
        name    = "disassemble",
        command = f"{DSD} {DSD_BASE_FLAGS} dis "
                  "--config-path $config_path "
                  "--asm-path $output_path "
                  "--ual")
    n.build(
        inputs    = p.dsd_configs(),
        rule      = "disassemble",
        outputs   = "dis",
        variables = {
            "config_path": str(p.arm9_config_yaml()),
            "output_path": str(p.arm9_disassembly_dir())})
    n.newline()


    # ############ LINKER PREPARING ############ #
    ##############################################
    ##############################################
    # ############# LINKER COMMAND  ############ #


    n.comment("The linker command.")
    LD       = DEFAULT_COMPILER_CONFIG.linker_bin()
    LCF_FILE = p.arm9_lcf_file()
    n.rule(
        name    = "mwld",
        command = f"{WIBO} {LD} {LD_FLAGS} "
                  "$extra_ld_flags "
                  "@$objects_file "
                  "$lcf_file "
                  "-o $out")
    # print(f"ARM 9 objects file: {p.arm9_objects_file()}")
    objects_to_link = [file["object_to_link"] for file in p.files()]
    if len(objects_to_link) > 0:
        n.build(
            inputs    = [*objects_to_link, LCF_FILE, p.arm9_objects_file()],
            implicit  = str(LD),
            rule      = "mwld",
            outputs   = str(p.arm9_o()),
            variables = {
                "extra_ld_flags": ARM9_LD_FLAGS,
                "lcf_file": str(LCF_FILE),
                "objects_file": str(p.arm9_objects_file())})
        n.newline()


    n.comment("The compilation command.")
    n.rule(
        name    = "mwcc",
        command = f"{WIBO} sumthin sumthing...")  # TODO: Work here
    n.newline()


    # TODO: Remove this...?
    n.build(
        inputs  = str(p.arm9_o()),
        rule    = "phony",
        outputs = "arm9")
    n.newline()


    n.comment("Verify that the generated rom matches with original.")
    n.rule(
        name    = "sha1",
        command = f"{SHA1} $in -c $sha_file")
    n.build(
        inputs    = str(OUT_FILE),
        rule      = "sha1",
        variables = {"sha_file": str(p.rom_sha1_file())},
        outputs   = "sha1")
    n.newline()


    n.default([
        # "objdiff",
        # "check",
        "sha1",
        # "report",
    ])




if __name__ == "__main__":
    main()

# vim:ts=4:sts=4:sw=4:cc=78:et:ai
