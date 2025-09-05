
# EXECUTABLE FILES
FASMARM=./tools/fasmarm
DSD=./tools/dsd

OBJDIFF=./tools/objdiff-cli
WIBO=./tools/wibo



###################################################
# SELECT A VERSION FOR MWCCARM
###################################################
# 1.2: base  sp2  sp2p3  sp3  sp4
# 2.0: base  sp1  sp1p2  sp1p5  sp1p6  sp1p7  sp2  sp2p2  sp2p3  sp2p4
# dsi: 1.1  1.1p1  1.2  1.2p1  1.2p2  1.3  1.3p1  1.6sp1  1.6sp2
MWCCARM_VER=2.0/sp1p5



###################################################
# SET UP THE LINKER COMMAND
###################################################
MWLD_EXE="./tools/mwccarm/$(MWCCARM_VER)/mwldarm.exe"
MWLD_FLAGS=-proc arm946e -dead -nostdlib -interworking -map closure,unused -msgstyle gcc 
MWLD_EXTRA_FLAGS=-m Entry
MWLD_OUTPUT_BINARY_ELF=$(BUILD_DIR)/linked_and_ready_to_go.elf

MWLD=$(WIBO) $(MWLD_EXE) $(MWLD_FLAGS) $(MWLD_EXTRA_FLAGS)

BUILD_DIR=./build
#
# rule mwld
#   command = ./wibo "./tools/mwccarm/2.0/sp1p5/mwldarm.exe" -proc arm946e $
#       -interworking -map closure,unused -msgstyle gcc -nodead -nostdlib $
#       $extra_ld_flags @$objects_file $lcf_file -o $out
# 
#		build/delinks/itcm_0.o \
#		build/delinks/dtcm_1.o \
#		build/delinks/main_4.o \
#
#		$(BUILD_DIR)/objects.txt \

link:
	$(MWLD) \
		$(BUILD_DIR)/arm9.lcf \
		build/delinks/itcm_0.o \
		build/delinks/dtcm_1.o \
		build/delinks/main_4.o \
		-o $(MWLD_OUTPUT_BINARY_ELF)




###################################################
# SET UP THE COMPILER COMMAND
###################################################
MWCC_EXE=./tools/mwccarm/$(MWCCARM_VER)/mwccarm.exe
MWCC_CFLAGS=-O4,p -enum int -char signed -str noreuse -proc arm946e -gccext,on -fp soft -inline noauto -lang=c
MWCC=$(WIBO) $(MWCC_EXE) $(MWCC_CFLAGS)
print-mmwc-strings:
	@#printf "mwcc exe: \t%s\n" $(MWCC_EXE)
	@#printf "mwcc flags:\n"
	@#printf "\t%s\n" $(MWCC_CFLAGS) 
	$(MWCC)



INPUT_ROM=./rom/atc.nds
ARM7_BIOS=./rom/bios7.bin
EXTRACT_DIR=./extract
dsd-extract:
	$(DSD) \
		rom extract \
		--arm7-bios $(ARM7_BIOS) \
		--rom $(INPUT_ROM) \
		--output-path $(EXTRACT_DIR)
	@printf "\nDSD extraction of %s\n\tmade to %s\n" \
		$(INPUT_ROM) \
		$(EXTRACT_DIR)



OUTPUT_ROM=./rom/out.nds
DSD_CONFIG_DIR=./dsd-config
ROM_CONFIGURATION_YAML=$(EXTRACT_DIR)/config.yaml
dsd-build:
	@printf "\nReplace old extracted roms with newly built ones.\n"
	$(DSD) \
		rom build \
		--arm7-bios $(ARM7_BIOS) \
		--config $(ROM_CONFIGURATION_YAML) \
		--rom $(OUTPUT_ROM)
	@printf "\nDSD rom build done: \n\t%s\n" $(OUTPUT_ROM)



dsd-init:
	$(DSD) \
		init \
		--rom-config $(ROM_CONFIGURATION_YAML) \
		--output-path $(DSD_CONFIG_DIR) \
		--build-path $(BUILD_DIR)
	@printf "\nDSD init into:\n\t%s\n\t%s\n" \
		$(DSD_CONFIG_DIR) \
		$(BUILD_DIR)



###################################################
## OPTIONAL STEP, FOR PERSONAL INDULGENCE
###################################################
ARM9_BINARY_CONFIGURATION=$(DSD_CONFIG_DIR)/arm9/config.yaml
ASM_OUT_DIR=./asm
dsd-disasm:
	$(DSD) \
		dis \
		--config-path $(ARM9_BINARY_CONFIGURATION) \
		--asm-path $(ASM_OUT_DIR) \
		--ual
	@printf "\nDSD disassembly was done in %s\n" $(ASM_OUT_DIR)
	@printf "\nNote: This is only for testing purposes."



###################################################
## DELINKING COMMAND
###################################################
dsd-delink:
	$(DSD) \
		delink \
		--config-path $(ARM9_BINARY_CONFIGURATION)
	@printf "\nDSD delinking done. "
	@printf "ELF files written to:\n\t%s/delinks.\n" $(BUILD_DIR)

dsd-delink-json:
	@printf "\nDelinking information in a nice JSON format:\n\n"
	@$(DSD) \
		json delink \
		--config-path $(ARM9_BINARY_CONFIGURATION)


dsd-lcf:
	$(DSD) \
		lcf \
		--config-path $(ARM9_BINARY_CONFIGURATION)


clean:
	rm -rf extract
	rm $(OUTPUT_ROM)
	@printf "clean done!\n"

