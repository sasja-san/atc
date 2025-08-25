
# Air Traffic Chaos

Air Traffic Chaos is a game for Nintendo DS.
This is a project to create a decompilation of it and/or to modify the game.










# Executables and Licenses 

The whole project is licensed under GLWTS, **EXCEPT** for binaries found in 
the `tools/` directory. These are covered under their own licenses.
The binaries provided have been compressed using `upx --best --lzma`.
Provided binaries are:

    * [dsd](https://github.com/AetiasHax/ds-decomp)
    * [fasmarm](https://arm.flatassembler.net)
    * [objdiff](https://github.com/encounter/objdiff)
    * [wibo](https://github.com/decompals/wibo)

Because GPL3 is an intolerable bullshit license, you'll have to provide a
binary for [m2c](https://github.com/matt-kempster/m2c) yourself.

Getting `mwccarm` is done through a download script and its licence should be
contained within the zip.











# Roms Needed

`sha1sum` in `./rom/` should yield this.
Either output for `bios7.bin` should be good (top one is DSi).
Use the USA rom of Air Traffic Chaos.

```{.txt}
4f36e459b6d2472c403a008a61140377a6c53229  atc.nds
24f67bdea115a2c847c8813a262502ee1607b7df  bios7.bin
6ee830c7f552c5bf194c20a2c13d5bb44bdb5c03  bios7.bin
```

Follow this guide to extract `bios7.bin` from a console:
<https://wiki.ds-homebrew.com/ds-index/ds-bios-firmware-dump>










# Project File Structure

Notable entries               | How it got there             | Current use
------------------------------|------------------------------|--------------------------------
`Makefile`                    | Needed automation            | Should contain the commands run most regularely.
`extract/`                    | `$ make dsd-extract`         | Metadata files, extracted by analyzing the rom, needed to re-build the rom.
`extract/files/`              | `$ make dsd-extract`         | Files from the NitroFS section of the rom.
`extract/files/data/rjff/`    | `$ make dsd-extract`         | Data files for the Fukuoka (first) stage. RJFF is its ICAO code.
`extract/config.yaml`         | `$ make dsd-extract`         | Configuration file for re-building the rom with `dsd rom build`.
`dsd-config/`                 | `$ make dsd-init`            | Place to store the ARM 9 binary metada. Needed in order to re-build the binary.
`dsd-config/arm9/symbols.txt` | `$ make dsd-init`            | A mapping of the ARM 9 binary. Through Ghidra use new symbols may noted here.
`rom/`                        | `$ mkdir rom`                | Storage location for `atc.nds` and `bios7.bin`.
`rom/out.nds`                 | `$ make dsd-build`           | This is the output rom.
`src/`                        | Started writing code         | C code from the reverse engineering efforts are placed here.
`tools/`                      | Needed a place for binaries  | Location for the tools this project utilizes. In `./Makefile` these should be referenced at the top.
`tools/mwccarm/`              | You ran a download script    | A collection (different versions) of C & C++ compilers. With the correct version your C code will match the original binary.











# Getting Started

















