# COMRADES - SNES build
# Needs PVSnesLib (PVSNESLIB_HOME) and Python 3 with Pillow.

ifeq ($(strip $(PVSNESLIB_HOME)),)
$(error "Please set PVSNESLIB_HOME to your PVSnesLib folder: https://github.com/alekmaul/pvsneslib/wiki/Installation")
endif

export ROMNAME := comrades
export ROMTITLE := COMRADES

include ${PVSNESLIB_HOME}/devkitsnes/snes_rules

.PHONY: assets all clean

GEN := tools/heroes.py tools/critters.py tools/ffa_stage.py tools/font.py tools/sprites_build.py tools/title.py

all: assets $(ROMNAME).sfc

build/.stamp: $(GEN) tools/pixel.py tools/snesgfx.py
	python3 tools/heroes.py
	python3 tools/critters.py
	python3 tools/ffa_stage.py
	python3 tools/font.py
	python3 tools/sprites_build.py
	python3 tools/title.py
	touch build/.stamp

assets: build/.stamp

src/data.obj: build/.stamp

clean: cleanBuildRes cleanRom
	rm -rf build
