# COMRADES - SNES build
# Needs PVSnesLib (PVSNESLIB_HOME) and Python 3 with Pillow.

ifeq ($(strip $(PVSNESLIB_HOME)),)
$(error "Please set PVSNESLIB_HOME to your PVSnesLib folder: https://github.com/alekmaul/pvsneslib/wiki/Installation")
endif

export ROMNAME := comrades
export ROMTITLE := COMRADES

# music and sound effects (SNESMOD); the effects module must come first
SMCONVFLAGS := -s -o build/soundbank -V -b 5 -f
AUDIOFILES := build/sfx.it build/title.it build/stage1.it build/clear.it
export SOUNDBANK := build/soundbank

include ${PVSNESLIB_HOME}/devkitsnes/snes_rules

.PHONY: assets all clean

GEN := tools/heroes.py tools/critters.py tools/ffa_stage.py tools/font.py tools/sprites_build.py tools/title.py tools/music.py

all: assets $(ROMNAME).sfc

$(AUDIOFILES): build/.stamp

build/.stamp: $(GEN) tools/pixel.py tools/snesgfx.py tools/itwriter.py
	python3 tools/heroes.py
	python3 tools/critters.py
	python3 tools/ffa_stage.py
	python3 tools/font.py
	python3 tools/sprites_build.py
	python3 tools/title.py
	python3 tools/music.py
	touch build/.stamp

assets: build/.stamp

src/data.obj: build/.stamp

clean: cleanBuildRes cleanRom
	rm -rf build
