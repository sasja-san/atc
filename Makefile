
# EXECUTABLE FILES
FASMARM=./tools/fasmarm
DSD=./tools/dsd

# ROM PATHS
INPUT_ROM=./rom/atc.nds
OUTPUT_ROM=./rom/out.nds
ARM7_BIOS=./rom/bios7.bin



EXTRACT_DIR=./extract
EXTRACT_CONFIG_YAML=$(EXTRACT_DIR)/config.yaml

DSD_CONFIG_DIR=./dsd-config
DSD_CONFIG_ARM9_CONFIG_FILE=$(DSD_CONFIG_DIR)/arm9/config.yaml


BUILD_PATH=./build
ASM_OUT_PATH=./asm

# The data files will land in a directory called 'data' 
NITRO_FS_DIR=./nitro_fs/

dsd-extract:
	$(DSD) \
		rom extract \
		--arm7-bios $(ARM7_BIOS) \
		--rom $(INPUT_ROM) \
		--output-path $(EXTRACT_DIR)
	@printf "\nDSD extraction of %s\n\tmade to %s\n" \
		$(INPUT_ROM) \
		$(EXTRACT_DIR)


dsd-build:
	$(DSD) \
		rom build \
		--arm7-bios $(ARM7_BIOS) \
		--config $(EXTRACT_CONFIG_YAML) \
		--rom $(OUTPUT_ROM)
	@printf "\nDSD rom build done: \n\t%s\n" $(OUTPUT_ROM)


dsd-init:
	$(DSD) \
		init \
		--rom-config $(EXTRACT_CONFIG_YAML) \
		--output-path $(DSD_CONFIG_DIR) \
		--build-path $(BUILD_PATH)
	@printf "DSD init into:\n\t%s\n\t%s\n" \
		$(DSD_CONFIG_DIR) \
		$(BUILD_PATH)

dsd-disasm:
	$(DSD) \
		dis \
		--config-path $(DSD_CONFIG_ARM9_CONFIG_FILE) \
		--asm-path $(ASM_OUT_PATH) \
		--ual



clean:
	rm -rf extract
	rm $(OUTPUT_ROM)
	@printf "clean done!\n"

