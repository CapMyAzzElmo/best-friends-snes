.include "hdr.asm"

; Stage 1: FFA Convention ------------------------------------------------------
.section ".rodata_stage1" superfree

stage1_bg1_pic:
.incbin "build/stage1_bg1.pic"
stage1_bg1_pic_end:

stage1_map:
.incbin "build/stage1.m16"

stage1_tiledef:
.incbin "build/stage1.t16"

stage1_tileprop:
.incbin "build/stage1.b16"

stage1_bg_pal:
.incbin "build/stage1_bg.pal"

stage1_hero:
.incbin "build/stage1_hero.o16"

.ends

.section ".rodata_stage1_bg2" superfree

stage1_bg2_pic:
.incbin "build/stage1_bg2.pic"
stage1_bg2_pic_end:

stage1_bg2_map:
.incbin "build/stage1_bg2.map"

.ends

; Title screen and UI -----------------------------------------------------------
.section ".rodata_ui" superfree

logo_pic:
.incbin "build/logo.pic"
logo_pic_end:

logo_pal:
.incbin "build/logo.pal"

title_bg1_map:
.incbin "build/title_bg1.map"

font_pic:
.incbin "build/font.pic"
font_pic_end:

ui_pal:
.incbin "build/ui.pal"

.ends

; Sprites -------------------------------------------------------------------------
.section ".rodata_jon" superfree

jon_pic:
.incbin "build/jon.pic"
jon_pal:
.incbin "build/jon.pal"
jon_dim_pal:
.incbin "build/jon_dim.pal"

.ends

.section ".rodata_wes" superfree

wes_pic:
.incbin "build/wes.pic"
wes_pal:
.incbin "build/wes.pal"
wes_dim_pal:
.incbin "build/wes_dim.pal"

.ends

.section ".rodata_critters" superfree

beasts_pic:
.incbin "build/beasts.pic"
small_pic:
.incbin "build/small.pic"
critters_pal:
.incbin "build/critters.pal"
pig_pal:
.incbin "build/pig.pal"

.ends
