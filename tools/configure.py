#!/usr/bin/env python3

import json
import os
from   pathlib     import Path
import argparse
import sys
import subprocess
from   dataclasses import dataclass
from   typing      import Any

import ninja_syntax

# from p_lib.get_platform import Platform, get_platform

def leave(*strs):
  for s in strs:
    print(s)
  exit(1)



ROOT_PATH = Path(".")

NINJA_FILE   = ROOT_PATH / "build.ninja"

EXTRACT_DIR  = ROOT_PATH / "extract"
BUILD_DIR    = ROOT_PATH / "build"
CONF_DIR     = ROOT_PATH / "dsd-config"
SRC_DIR      = ROOT_PATH / "src"               # game
INC_DIR      = ROOT_PATH / "include"           # headers
LIBS_DIR     = ROOT_PATH / "libs"              # libraries used
LIBS_INC_DIR = ROOT_PATH / "libs" / "include"  # this is pure magic...?

ROM_FILE     = ROOT_PATH / "rom" / "atc.nds"
OUT_FILE     = ROOT_PATH / "rom" / "out.nds"   # The output ROM
BIOS_FILE    = ROOT_PATH / "rom" / "bios7.bin" # optional

WIBO         = ROOT_PATH / "tools" / "wibo"
DSD          = ROOT_PATH / "tools" / "dsd"
OBJDIFF      = ROOT_PATH / "tools" / "objdiff"
OBJDIFF_CLI  = ROOT_PATH / "tools" / "objdiff-cli"
MWCC_DIR     = ROOT_PATH / "tools" / "mwccarm"

DECOMP_ME_COMPILER = "mwcc_30_131"




@dataclass(frozen=True)
class CompilerConfig:
  version: str
  flags:   str

  def compiler_bin(self): 
    return os.path.join(".", MWCC_DIR / self.version / "mwccarm.exe")

  def linker_bin(self): 
    return os.path.join(".", MWCC_DIR / self.version / "mwldarm.exe")


# Used when source not found in PER_SOURCE_COMPILER_CONFIGS.
DEFAULT_COMPILER_CONFIG = CompilerConfig(
  version = "2.0/sp1p5",
  flags   = (
    "-O4,p",           # Leave this as first arg!

    "-enum int",       # Use int-sized enums
    "-char signed",    # Char type is signed
    "-proc arm946e",   # Target processor
    "-gccext,on",      # Enable GCC extensions
    "-fp soft",        # Compute float operations in software
    "-inline noauto",  # Inline only functions marked with 'inline'
    "-RTTI off",       # Disable runtime type information
    "-interworking",   # Enable ARM/Thumb interworking
    "-w off",          # Disable warnings
    "-sym on",         # Debug info, including line numbers
    "-gccinc",         # Interpret #include "..." and #include <...> equally
    "-nolink",         # Do not link
    "-msgstyle gcc",   # Use GCC-like messages (helsp some IDEs)
    "-enc SJIS",       # Use Shift-JIS encoding
    # FIX: Add string reuse and exception flags
    ""

    "-ipa file"        # Leave this as last arg!
  )
)

PER_SOURCE_COMPILER_CONFIGS: dict[Path, CompilerConfig] = {
  Path(SRC_DIR / "some_dir" / "some_file.c"): CompilerConfig(
    version = "1.2/sp4",
    flags   = (
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
  return PER_SOURCE_COMPILER_CONFIGS.get(rel_p, DEFAULT_COMPILER_CONFIG)


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
MODULE_LD_FLAGS = " ".join([ "-library" ])

# Only passed to the final arm9.o link. Sets entry function.
ARM9_LD_FLAGS = " ".join([ "-m Entry" ])

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

DSD_BASE_FLAGS = " ".join([ "--force-color" ])

# for more advance stuff, see TWEWY code
CC_INCLUDES = " ".join( [ f"-i {INC_DIR}", f"-i {LIBS_INC_DIR}" ] )



# p = Project(args.version, platform=platform, delinks_json=delinks_json)
class Project:
  def __init__(self, delinks_json: Any | None):

    self.delinks_json = delinks_json #delinks JSON data from dsd

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
      files.append( str(src_obj_path.with_suffix(".o") ))
    return files

  def arm9_o(self) -> Path:
    return self.game_build / "arm9.o"

  def arm9_disassembly_dir(self) -> Path:
    return self.game_build / "asm"

  def objdiff_report(self) -> Path:
    return self.game_build / "report.json"

  def files(self) -> list[ dict[str,str] ]:
    if self.delinks_json is None:
      return []
    return self.delinks_json["files"]

  def delink_files(self) -> list[str]:
    delink_files = [file["delink_file"] for file in self.files()]
    return list(set(delink_files))

  def arm9_lcf_file(self) -> str:
    if self.delinks_json is None:
      return ""
    return self.delinks_json["arm9_objects_file"]



def get_c_cpp_files(dirs: list[Path]):
  for dir in dirs:
    for root, _, files in os.walk(dir):
      root = Path(root)
      for file in files:
        if is_cpp(file) or is_c(file):
          yield root / file


def main():

  if Path.cwd().name != "atc":
    leave("Not runnig from project root directory!", "Exiting...")
  if not MWCC_DIR.is_dir():
    leave(
      f"Could not locate MWCC directory: {MWCC_DIR}",
      "Run this to download the compiler collection:",
      "    $ tools/get_mwccarm.sh")
  if not DSD.exists():
    leave(f"Could not find program: {DSD}")

  out = subprocess.run(
    [
      DSD,
      "--force-color",
      "json",
      "delinks",
      "--config-path",
      f"{CONF_DIR / 'arm9' / 'config.yaml'}"
    ],
    capture_output = True,
    text = True,
  )
  if out.returncode != 0:
    leave("Error running dsd:", f"{out.stderr.strip()}")

  delinks_json = json.loads(out.stdout)

  
  with NINJA_FILE.open("w") as file:
    n = ninja_syntax.Writer(file)
    p = Project(delinks_json = delinks_json)

    n.comment("Arm7 bios file is optional, but highly recomended.")
    if BIOS_FILE.is_file():
      n.variable("arm7_bios_flag", f"--arm7-bios {BIOS_FILE}")
    else:
      n.variable("arm7_bios_flag", "")
    n.newline()


    n.rule(
      name    = "extract",
      command = 
        f"{DSD} {DSD_BASE_FLAGS} rom extract "
        "--output-path $output_path --rom $in $arm7_bios_flag" )
    n.build(
      inputs    = str(ROM_FILE),
      rule      = "extract",
      outputs   = str(p.baserom_config()), # extract/config.yaml
      variables = {"output_path": str(EXTRACT_DIR) } )
    n.newline()

    n.rule(
      name    = "delink",
      command =
        f"{DSD} {DSD_BASE_FLAGS} delink "
        "--config-path $config_path")
    n.build(
      inputs    = p.dsd_configs() + [ str(p.baserom_config()) ],
      # implicit  = DSD,
      rule      = "delink",
      outputs   = p.delink_files(),
      variables = {
        "config_path": str(p.arm9_config_yaml()),
      },
    )
    

  return 0




if __name__ == "__main__":
  main()

# vim:ts=2:sts=2:sw=2:cc=78:et:ai
