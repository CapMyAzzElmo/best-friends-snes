# COMRADES - SNES build
# Needs PVSnesLib (PVSNESLIB_HOME) and Python 3 with Pillow.

ifeq ($(strip $(PVSNESLIB_HOME)),)
$(error "Please set PVSNESLIB_HOME to your PVSnesLib folder: https://github.com/alekmaul/pvsneslib/wiki/Installation")
endif

export ROMNAME := comrades
export ROMTITLE := COMRADES
# 1MB LoROM
export ROMSIZE := 0A
export ROMBANKS := 32
export FASTROM := 1

# music and sound effects (SNESMOD); the effects module must come first
SMCONVFLAGS := -s -o build/soundbank -V -b 5 -f
AUDIOFILES := build/sfx.it build/title.it build/stage1.it build/stage2.it build/stage3.it build/stage4.it \
	build/stage5.it build/stage6.it build/boss.it build/clear.it build/race.it build/range.it build/ending.it
export SOUNDBANK := build/soundbank

include ${PVSNESLIB_HOME}/devkitsnes/snes_rules

.PHONY: assets all clean

STAGES := tools/stages/s1_ffa.py tools/stages/s2_jam.py tools/stages/s3_bar.py tools/stages/s4_chicago.py \
	tools/stages/s5_court.py tools/stages/s6_golden.py
GEN := tools/heroes.py tools/critters.py tools/sprites_build.py $(STAGES) tools/stagekit.py tools/foes.py tools/items.py \
	tools/bonus.py tools/font.py tools/title.py tools/music.py tools/gen_data.py

all: assets $(ROMNAME).sfc

$(AUDIOFILES): build/.stamp

build/.stamp: $(GEN) tools/pixel.py tools/snesgfx.py tools/itwriter.py
	mkdir -p build
	python3 tools/heroes.py
	python3 tools/sprites_build.py
	for s in $(STAGES); do python3 $$s || exit 1; done
	python3 tools/foes.py
	python3 tools/items.py
	python3 tools/bonus.py
	python3 tools/font.py
	python3 tools/title.py
	python3 tools/music.py
	python3 tools/gen_data.py
	touch build/.stamp

assets: build/.stamp

src/data.obj: build/.stamp
src/assets.ps src/main.ps src/stage.ps src/boss.ps src/race.ps src/range.ps: build/.stamp $(SOUNDBANK).asm

clean: cleanBuildRes cleanRom
	rm -rf build
