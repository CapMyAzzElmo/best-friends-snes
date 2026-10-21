"""Stage 2: Jam Sessions. Learning guitar together at Wes's house: the living
room (couches, coffee tables, bookshelves), the hallway, then the garage
jam space full of amp stacks and speaker towers, where a feedback-howling
amp stack waits.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pixel import Canvas, capsule, ellipse, shade, outlined
from stagekit import (Level, T_EMPTY, T_SOLID, T_PLATE, PAL_A, PAL_B, PAL_C, PAL_D,
                      FOE_A, FOE_B, FOE_C, ARENA_MT, noise, fill, frame_box, export_stage,
                      pal_grid, set_pal_rect)

P_HOUSE = [(0, 0, 0), (30, 20, 24),
           (204, 148, 96), (164, 110, 68), (118, 76, 46),          # 2-4 hardwood
           (120, 160, 104), (84, 120, 74), (52, 80, 52),           # 5-7 couch green
           (46, 44, 54), (82, 80, 94),                             # 8-9 amp tolex
           (66, 60, 66),                                           # 10 grill cloth
           (196, 196, 206),                                        # 11 chrome
           (238, 224, 190),                                        # 12 cream piping
           (210, 176, 120),                                        # 13 tweed
           (196, 62, 50),                                          # 14 red
           (250, 250, 240)]                                        # 15 white
P_STUFF = [(0, 0, 0), (30, 20, 24),
           (248, 184, 72), (210, 112, 44), (128, 48, 28),          # 2-4 sunburst guitar
           (96, 120, 186), (64, 80, 140), (40, 50, 96),            # 5-7 rug blue
           (238, 224, 190),                                        # 8 cream
           (40, 36, 40),                                           # 9 black
           (90, 172, 160), (52, 118, 112),                         # 10-11 teal
           (230, 210, 90),                                         # 12 lamp yellow
           (150, 96, 160),                                         # 13 purple
           (196, 62, 50),                                          # 14 red
           (250, 250, 240)]                                        # 15 white
P_WALL = [(0, 0, 0), (26, 22, 30),
          (150, 120, 96), (126, 98, 78), (104, 80, 64),           # 2-4 wallpaper
          (176, 146, 116),                                        # 5 wallpaper light stripe
          (94, 62, 44), (128, 88, 60),                            # 6-7 wainscot wood
          (60, 40, 30),                                           # 8 dark trim
          (40, 56, 96), (70, 92, 150), (230, 140, 90),            # 9-11 dusk window
          (250, 200, 120),                                        # 12 sun glow
          (84, 70, 62),                                           # 13 shelf
          (160, 132, 104),                                        # 14 frame
          (230, 220, 200)]                                        # 15 cream
P_POSTER = [(0, 0, 0), (26, 22, 30),
            (210, 70, 60), (240, 200, 80), (60, 120, 200),         # 2-4 poster primaries
            (30, 30, 34), (240, 240, 230),                         # 5-6 black/white
            (120, 180, 90), (180, 90, 170),                        # 7-8 green/purple
            (90, 60, 50), (140, 100, 70),                          # 9-10 records sleeves
            (60, 50, 56),                                          # 11 vinyl
            (200, 160, 110), (150, 110, 80),                       # 12-13 cork
            (110, 84, 64), (250, 220, 150)]                        # 14-15


# --- metatiles -----------------------------------------------------------------
def mt_floor_top():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            board = (y // 4)
            seam = (x + board * 5) % 16 == 0
            n = noise(x // 3, y, 41 + board)
            c.set(x, y, 4 if seam or y % 4 == 3 else (2 if n > 0.82 else 3))
    for x in range(16):
        c.set(x, 0, 1)
        c.set(x, 1, 2)
    return c, PAL_A, [T_SOLID] * 4


def mt_floor():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            c.set(x, y, 4 if (y % 4 == 3 or (x + (y // 4) * 7) % 16 == 0) else (3 if noise(x, y, 43) > 0.7 else 4 if y > 10 else 3))
    return c, PAL_A, [T_SOLID] * 4


def couch(w_mt):
    """Green couch: seat cushions are a one-way platform at the top row."""
    w = w_mt * 16
    c = Canvas(w, 32)
    fill(c, 0, 4, w, 28, 6)
    fill(c, 0, 0, 10, 28, 5)
    fill(c, w - 10, 0, w, 28, 5)
    for x0 in range(10, w - 10, 20):              # cushions
        fill(c, x0 + 1, 4, min(x0 + 20, w - 10) - 1, 14, 5)
        for x in range(x0 + 1, min(x0 + 20, w - 10) - 1):
            c.set(x, 4, 12); c.set(x, 13, 7)
    for y in range(4, 28):
        c.set(9, y, 7); c.set(w - 10, y, 7)
    fill(c, 0, 26, w, 28, 7)
    for x in (4, w - 5):                          # wooden feet
        fill(c, x - 1, 28, x + 2, 32, 4)
    shade(c, 6, 5, 7)
    o = outlined(c, 1)
    for x in range(w):
        o.set(x, 0, 1 if c.get(x, 0) else 0)
    return o


def coffee_table(w_mt):
    w = w_mt * 16
    c = Canvas(w, 16)
    fill(c, 0, 0, w, 4, 3)
    for x in range(w):
        c.set(x, 0, 2); c.set(x, 3, 4)
    for x in (2, w - 4):
        fill(c, x, 4, x + 2, 16, 4)
    # a mug and a guitar pick on top would read as clutter: keep it clean
    return outlined(c, 1)


def bookshelf(h_mt):
    c = Canvas(32, h_mt * 16)
    fill(c, 0, 0, 32, c.h, 4)
    for y0 in range(0, c.h, 16):
        fill(c, 2, y0 + 3, 30, y0 + 15, 8)
        x = 3
        k = 0
        while x < 29:
            bw = 2 + int(noise(x, y0, 51) * 3)
            col = [14, 5, 12, 13, 9, 6][int(noise(x, y0, 53) * 6)]
            top = y0 + 4 + int(noise(x, y0, 57) * 4)
            fill(c, x, top, min(x + bw, 29), y0 + 15, col)
            x += bw + (1 if noise(x, y0, 59) > 0.6 else 0)
            k += 1
        for x in range(32):
            c.set(x, y0, 2); c.set(x, y0 + 1, 3)
    o = outlined(c, 1)
    frame_box(o, 0, 0, 32, c.h, 1)
    return o


def amp(big=False):
    """Amp head/cab: tolex box, grill cloth, chrome corners, knobs."""
    h = 32
    c = Canvas(32, h)
    fill(c, 0, 0, 32, h, 8)
    fill(c, 3, 9 if not big else 3, 29, h - 3, 10)
    for y in range(9 if not big else 3, h - 3):     # grill weave
        for x in range(3, 29):
            if (x + y) % 3 == 0:
                c.set(x, y, 9)
    if not big:
        fill(c, 3, 2, 29, 7, 13)                     # control panel
        for kx in range(6, 28, 4):
            c.set(kx, 4, 11); c.set(kx, 5, 1)
        c.set(26, 3, 14)                             # power light
    for (x, y) in ((1, 1), (30, 1), (1, h - 2), (30, h - 2)):
        c.set(x, y, 11)
    o = outlined(c, 1)
    frame_box(o, 0, 0, 32, h, 1)
    return o


def speaker_tower():
    c = Canvas(32, 64)
    fill(c, 0, 0, 32, 64, 8)
    for cy in (14, 40):
        ellipse(c, 16, cy, 11, 11, 9)
        ellipse(c, 16, cy, 8, 8, 10)
        ellipse(c, 16, cy, 3, 3, 11)
    ellipse(c, 16, 58, 3, 2, 11)
    o = outlined(c, 1)
    frame_box(o, 0, 0, 32, 64, 1)
    return o


def guitar_case():
    c = Canvas(48, 16)
    ellipse(c, 10, 8, 9, 7, 8)
    ellipse(c, 26, 8, 7, 6, 8)
    fill(c, 26, 5, 46, 11, 8)
    shade(c, 8, 9, 8)
    for x in range(4, 44, 9):
        c.set(x, 8, 11)
    o = outlined(c, 1)
    # pad to whole metatiles (sits on the floor)
    return o


def rug(w_mt):
    w = w_mt * 16
    c = Canvas(w, 16)
    for x in range(w):
        for y in range(12, 16):
            c.set(x, y, 6 if (x // 4 + y) % 2 else 5)
        c.set(x, 12, 7); c.set(x, 15, 7)
    return c


def floor_hatch(part):
    """Open hatch to the basement, cables dangling into the dark."""
    c = Canvas(16, 32)
    fill(c, 0, 4, 16, 32, 1)
    for y in range(4, 32):
        for x in range(16):
            if (x + y * 3) % 7 == 0 and y > 8:
                c.set(x, y, 8)
    if part == 1 or part == 0:
        capsule(c, (6, 4), (8, 20), 0.6, 9)
    if part != 0:
        capsule(c, (11, 4), (9, 26), 0.6, 14)
    for x in range(16):
        c.set(x, 3, 4); c.set(x, 4, 1)
    fill(c, 0, 28, 16, 32, 8)
    if part == 0:
        fill(c, 0, 0, 2, 32, 4)
    if part == 2:
        fill(c, 14, 0, 16, 32, 4)
    return c


def stairs_step(w_mt):
    w = w_mt * 16
    c = Canvas(w, 16)
    fill(c, 0, 0, w, 16, 3)
    for x in range(w):
        c.set(x, 0, 2); c.set(x, 1, 2); c.set(x, 15, 4)
    for y in range(16):
        c.set(0, y, 4); c.set(w - 1, y, 4)
    return outlined(c, 1)


def drum_kit():
    c = Canvas(48, 32)
    ellipse(c, 24, 20, 10, 10, 14)                 # kick drum
    ellipse(c, 24, 20, 8, 8, 15)
    ellipse(c, 24, 20, 3, 3, 14)
    ellipse(c, 10, 14, 6, 3, 14)                   # tom
    ellipse(c, 38, 14, 6, 3, 14)
    capsule(c, (4, 6), (16, 4), 0.8, 2)            # cymbals
    capsule(c, (34, 3), (46, 5), 0.8, 2)
    capsule(c, (10, 5), (10, 30), 0.5, 11)
    capsule(c, (40, 5), (40, 30), 0.5, 11)
    return outlined(c, 1)


def mic_stand():
    c = Canvas(16, 48)
    capsule(c, (8, 6), (8, 46), 0.6, 11)
    capsule(c, (8, 10), (13, 6), 0.5, 11)
    ellipse(c, 13, 5, 2, 2, 9)
    capsule(c, (3, 46), (13, 46), 0.7, 9)
    return outlined(c, 1)


# --- level -------------------------------------------------------------------
LEVEL_W_MT = 184


def build_level():
    lv = Level(LEVEL_W_MT)
    lv.floor(mt_floor_top(), mt_floor())
    A = PAL_A
    B = PAL_B

    def couches(mx, w=4):
        lv.platform(mx, 10, couch(w), A)

    def table(mx, w=2):
        lv.put_big(mx, 11, coffee_table(w), A, plate_top=True)

    def shelf(mx, h):
        lv.put_big(mx, 12 - h, bookshelf(h), A, plate_top=True)

    def amps(mx, my, big=False):
        lv.solid(mx, my, amp(big), A)

    def steps(mx, my, w):
        lv.platform(mx, my, stairs_step(w), A)

    def hatch(mx, n):
        lv.hazard(mx, n, floor_hatch, A)

    # A: the living room
    lv.deco(4, 11, rug(6), B)
    couches(10, 4)
    table(16, 2)
    shelf(20, 3)
    lv.foe(FOE_A, 25, 23, 30)                       # cat
    couches(31, 5)
    lv.foe(FOE_C, 33, 31, 36, row=10)               # sour note over the couch
    shelf(38, 4)
    steps(41, 9, 2)
    steps(44, 7, 2)
    lv.heart(45, 6)
    shelf(47, 3)
    table(51, 3)
    hatch(55, 3)
    lv.foe(FOE_B, 62, 58, 68)                       # walking amp
    # B: the hallway stairs
    steps(70, 10, 2)
    steps(72, 8, 2)
    steps(74, 6, 4)
    lv.foe(FOE_C, 76, 74, 78, row=6)
    steps(78, 8, 2)
    steps(80, 10, 2)
    hatch(83, 2)
    couches(86, 4)
    lv.foe(FOE_A, 92, 90, 98)
    shelf(99, 4)
    shelf(101, 3)
    hatch(104, 3)
    # C: the garage jam space
    lv.deco(109, 9, drum_kit(), B)
    amps(113, 10)
    amps(115, 10)
    amps(115, 8, big=True)
    lv.foe(FOE_C, 119, 117, 123, row=9)
    amps(119, 10)                                   # a step up to the speaker
    lv.solid(121, 8, speaker_tower(), A)
    lv.foe(FOE_B, 128, 124, 134)
    lv.deco(126, 11, guitar_case(), A)
    amps(135, 10)
    steps(137, 8, 3)
    lv.heart(138, 7)
    amps(141, 10, big=True)
    amps(141, 8)
    lv.foe(FOE_A, 147, 145, 152)
    hatch(153, 2)
    lv.deco(156, 9, mic_stand(), A)
    amps(158, 10)
    lv.foe(FOE_C, 162, 160, 166, row=9)
    amps(162, 10)
    lv.solid(164, 8, speaker_tower(), A)
    # D: the jam stage (boss arena)
    a0 = LEVEL_W_MT - ARENA_MT
    lv.deco(a0 + 1, 9, mic_stand(), A)
    steps(a0 + 3, 9, 3)
    steps(a0 + 10, 9, 3)
    lv.deco(a0 + 6, 11, rug(4), B)
    lv.start()
    return lv


# --- BG2: living room wall --------------------------------------------------------
def backdrop():
    W, H = 512, 224
    c = Canvas(W, H)
    pal = pal_grid(PAL_C)
    # ceiling and crown moulding
    fill(c, 0, 0, W, 24, 4)
    for x in range(W):
        c.set(x, 20, 8); c.set(x, 21, 7); c.set(x, 22, 6); c.set(x, 23, 8)
    # striped wallpaper with a little damask dot
    for y in range(24, 150):
        for x in range(W):
            stripe = (x // 8) % 4
            col = 3 if stripe in (0, 2) else (2 if stripe == 1 else 5)
            if stripe == 3 and (y // 8) % 2 == 0 and x % 8 == 4 and y % 8 == 4:
                col = 4
            c.set(x, y, col)
    # wainscot below
    for y in range(150, 224):
        for x in range(W):
            panel = x % 64
            col = 6 if panel in (0, 1, 62, 63) or y in (150, 151) else 7
            if y == 152 or y == 153:
                col = 8
            c.set(x, y, col)
    # windows at dusk (period 256)
    for x0 in (40, 296):
        fill(c, x0 - 2, 44, x0 + 50, 112, 14)
        for y in range(46, 110):
            g = (y - 46) / 64
            col = 9 if g < 0.35 else (10 if g < 0.7 else 11)
            if g > 0.9:
                col = 12
            for x in range(x0, x0 + 48):
                c.set(x, y, col)
        for y in range(46, 110):
            c.set(x0 + 23, y, 14); c.set(x0 + 24, y, 14)
        for x in range(x0, x0 + 48):
            c.set(x, 77, 14)
        fill(c, x0 - 6, 112, x0 + 54, 116, 13)   # sill
    # record shelf and posters (palette D)
    for x0 in (136, 392):
        fill(c, x0, 40, x0 + 40, 96, 6)          # poster
        fill(c, x0 + 2, 42, x0 + 38, 94, 5)
        ellipse(c, x0 + 20, 62, 12, 12, 2)       # bold circle graphic
        ellipse(c, x0 + 20, 62, 6, 6, 3)
        fill(c, x0 + 6, 80, x0 + 34, 84, 6)       # band name bar
        fill(c, x0 + 6, 87, x0 + 26, 89, 3)
        set_pal_rect(pal, x0, 40, x0 + 40, 96, PAL_D)
    for x0 in (196, 452):
        fill(c, x0, 104, x0 + 48, 108, 13)       # shelf plank
        for k in range(7):
            col = [9, 10, 11, 9, 10, 2, 11][k]
            fill(c, x0 + 2 + k * 6, 84, x0 + 7 + k * 6, 104, col)
        set_pal_rect(pal, x0, 80, x0 + 48, 104, PAL_D)
        # fix the shelf plank back to wall palette colors
    for x0 in (196, 452):
        for x in range(x0, x0 + 48):
            for y in range(104, 108):
                c.set(x, y, 13)
    # framed photo of the two friends (simple silhouettes)
    for x0 in (98, 354):
        fill(c, x0, 124, x0 + 24, 144, 14)
        fill(c, x0 + 2, 126, x0 + 22, 142, 15)
        ellipse(c, x0 + 8, 132, 3, 3, 4)
        ellipse(c, x0 + 16, 133, 3, 3, 4)
        fill(c, x0 + 5, 136, x0 + 20, 142, 4)
    return c, pal


def main():
    lv = build_level()
    bg2, bg2pal = backdrop()
    export_stage(2, lv, bg2, bg2pal, (P_HOUSE, P_STUFF, P_WALL, P_POSTER), (26, 22, 30))


if __name__ == "__main__":
    main()
