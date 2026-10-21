"""Stage 5: The Courthouse. Working the night shift as janitors in a
castle-like old courthouse: marble halls, stone pillars, stained glass,
courtroom pews, flooded basement grates, and the grand courtroom where the
Judge holds court.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pixel import Canvas, capsule, ellipse, shade, outlined
from stagekit import (Level, T_EMPTY, T_SOLID, T_PLATE, PAL_A, PAL_B, PAL_C, PAL_D,
                      FOE_A, FOE_B, FOE_C, ARENA_MT, noise, fill, frame_box, export_stage,
                      pal_grid, set_pal_rect)

P_STONE = [(0, 0, 0), (18, 16, 26),
           (236, 232, 222), (204, 198, 188), (166, 160, 152),     # 2-4 marble light
           (80, 76, 86), (56, 52, 62),                            # 5-6 marble dark
           (148, 140, 130), (118, 110, 104), (88, 82, 80),        # 7-9 stone block
           (230, 190, 90), (180, 136, 54),                        # 10-11 gold trim
           (70, 120, 160), (130, 180, 210),                       # 12-13 water
           (60, 44, 40),                                          # 14 grate iron
           (250, 250, 244)]                                       # 15 white
P_JANITOR = [(0, 0, 0), (18, 16, 26),
             (250, 214, 60), (210, 160, 30), (150, 100, 20),      # 2-4 janitor yellow
             (140, 90, 56), (104, 64, 40), (70, 42, 28),          # 5-7 pew wood
             (170, 40, 44), (120, 26, 34),                        # 8-9 red carpet / velvet
             (200, 200, 210), (140, 140, 150),                    # 10-11 steel
             (90, 150, 200),                                      # 12 mop water
             (230, 190, 90),                                      # 13 brass
             (30, 30, 34),                                        # 14 black
             (250, 250, 244)]                                     # 15 white
P_HALL = [(0, 0, 0), (12, 10, 20),
          (70, 66, 82), (56, 52, 68), (44, 40, 56),               # 2-4 wall stone
          (88, 84, 100),                                          # 5 stone light
          (30, 28, 40),                                           # 6 deep shadow
          (110, 90, 70), (80, 64, 50),                            # 7-8 wood beam
          (240, 220, 160),                                        # 9 candle glow
          (40, 36, 54),                                           # 10 arch shadow
          (60, 40, 70),                                           # 11 dim purple
          (150, 140, 160),                                        # 12 moonlight
          (34, 30, 46), (100, 96, 114), (24, 22, 34)]             # 13-15
P_GLASS = [(0, 0, 0), (12, 10, 20),
           (200, 60, 60), (240, 120, 100),                        # 2-3 red glass
           (60, 90, 200), (120, 160, 240),                        # 4-5 blue glass
           (230, 200, 70), (250, 240, 150),                       # 6-7 gold glass
           (70, 160, 90), (140, 220, 150),                        # 8-9 green glass
           (40, 36, 54),                                          # 10 lead came
           (130, 30, 40), (90, 20, 30),                           # 11-12 banner red
           (230, 190, 90),                                        # 13 banner gold
           (70, 66, 82), (56, 52, 68)]                            # 14-15 = wall stone


def mt_marble_top():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            checker = ((x // 8) + (y // 8)) % 2
            col = 3 if checker == 0 else 5
            v = noise(x, y, 111)
            if checker == 0 and v > 0.85:
                col = 4
            if checker == 1 and v > 0.85:
                col = 6
            c.set(x, y, col)
    for x in range(16):
        c.set(x, 0, 1); c.set(x, 1, 2); c.set(x, 2, 10); c.set(x, 3, 11)
    return c, PAL_A, [T_SOLID] * 4


def mt_foundation():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            seam = y % 8 == 7 or (x + (y // 8) * 8) % 16 == 15
            c.set(x, y, 9 if seam else (8 if noise(x, y, 113) > 0.3 else 7))
    return c, PAL_A, [T_SOLID] * 4


def stone_block(w_mt, h_mt):
    w, h = w_mt * 16, h_mt * 16
    c = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            course = y // 8
            seam = y % 8 == 7 or (x + (course % 2) * 8) % 16 == 15
            c.set(x, y, 9 if seam else (7 if y % 8 == 0 else 8))
    frame_box(c, 0, 0, w, h, 1)
    return c


def ledge(w_mt):
    w = w_mt * 16
    c = Canvas(w, 16)
    for x in range(w):
        c.set(x, 0, 1); c.set(x, 1, 2); c.set(x, 2, 3); c.set(x, 3, 3); c.set(x, 4, 4)
        c.set(x, 5, 10); c.set(x, 6, 11); c.set(x, 7, 1)
        if x % 8 in (2, 3, 4, 5):               # corbels
            for y in range(8, 12 - int(abs(x % 8 - 3.5))):
                c.set(x, y, 8)
    return c


def pillar(h_mt):
    c = Canvas(32, h_mt * 16)
    h = c.h
    fill(c, 6, 10, 26, h - 8, 3)
    for x in (8, 12, 16, 20, 24):                  # fluting
        for y in range(10, h - 8):
            c.set(x, y, 4)
    for y in range(10, h - 8):
        c.set(6, y, 2); c.set(25, y, 5)
    fill(c, 2, 2, 30, 10, 3)                        # capital
    for x in range(2, 30):
        c.set(x, 2, 2); c.set(x, 9, 10)
    ellipse(c, 6, 7, 3, 3, 4); ellipse(c, 26, 7, 3, 3, 4)
    fill(c, 3, h - 8, 29, h, 3)                     # base
    for x in range(3, 29):
        c.set(x, h - 8, 2); c.set(x, h - 1, 4)
    return outlined(c, 1)


def pew(w_mt):
    w = w_mt * 16
    c = Canvas(w, 32)
    fill(c, 0, 0, w, 20, 6)                          # high back
    for x in range(w):
        c.set(x, 0, 5); c.set(x, 1, 5)
    for x0 in range(4, w - 4, 12):
        frame_box(c, x0, 4, x0 + 9, 16, 7)
    fill(c, 0, 18, w, 24, 5)                         # seat
    fill(c, 0, 24, w, 32, 7)
    for x in (0, w - 1):
        for y in range(0, 32):
            c.set(x, y, 7)
    return outlined(c, 1)


def mop_bucket():
    c = Canvas(16, 32)
    fill(c, 2, 18, 14, 30, 2)
    for x in range(2, 14):
        c.set(x, 18, 3); c.set(x, 29, 4)
    fill(c, 3, 16, 13, 18, 12)                       # dirty water
    capsule(c, (5, 30), (5, 31), 1, 11); capsule(c, (11, 30), (11, 31), 1, 11)
    capsule(c, (10, 17), (13, 1), 0.6, 5)            # mop handle
    for dx in range(-2, 3):
        capsule(c, (10, 17), (10 + dx * 1.5, 23), 0.5, 15)
    return outlined(c, 1)


def wet_floor_sign():
    c = Canvas(16, 32)
    pts = [(8, 8), (2, 30), (14, 30)]
    for y in range(8, 31):
        half = (y - 8) * 6 / 22
        for x in range(int(8 - half), int(8 + half) + 1):
            c.set(x, y, 2)
    for y in range(8, 31):
        half = (y - 8) * 6 / 22
        c.set(int(8 + half), y, 3)
    ellipse(c, 8, 20, 2, 2, 14)                      # slipping figure
    capsule(c, (8, 22), (6, 27), 0.6, 14)
    return outlined(c, 1)


def judge_bench():
    c = Canvas(64, 48)
    fill(c, 0, 4, 64, 48, 6)
    fill(c, 0, 0, 64, 6, 5)
    for x in range(64):
        c.set(x, 0, 13); c.set(x, 5, 7)
    for x0 in range(4, 60, 14):
        frame_box(c, x0, 12, x0 + 11, 42, 7)
        fill(c, x0 + 2, 14, x0 + 9, 40, 5)
    ellipse(c, 32, 26, 8, 8, 13)                     # seal
    ellipse(c, 32, 26, 6, 6, 4)
    return outlined(c, 1)


def chandelier():
    c = Canvas(32, 32)
    capsule(c, (16, 0), (16, 10), 0.5, 13)
    capsule(c, (4, 16), (28, 16), 0.8, 13)
    capsule(c, (4, 16), (16, 10), 0.5, 13)
    capsule(c, (28, 16), (16, 10), 0.5, 13)
    for x in (4, 10, 16, 22, 28):
        fill(c, x - 1, 12, x + 1, 16, 15)
        c.set(x, 11, 2)
    return outlined(c, 1)


def grate(part):
    c = Canvas(16, 32)
    fill(c, 0, 6, 16, 28, 12)
    for y in range(6, 28):
        for x in range(16):
            if (x * 2 + y) % 10 == 0:
                c.set(x, y, 13)
    for x in range(16):
        c.set(x, 5, 14)
        if x % 4 == 0:
            for y in range(0, 6):
                c.set(x, y, 14)
    fill(c, 0, 28, 16, 32, 9)
    if part == 0:
        fill(c, 0, 0, 2, 28, 7)
    if part == 2:
        fill(c, 14, 0, 16, 28, 7)
    return c


def carpet(w_mt):
    w = w_mt * 16
    c = Canvas(w, 16)
    for x in range(w):
        for y in range(13, 16):
            c.set(x, y, 8 if y > 13 else 13)
    return c


LEVEL_W_MT = 196


def build_level():
    lv = Level(LEVEL_W_MT)
    lv.floor(mt_marble_top(), mt_foundation())
    A, B = PAL_A, PAL_B

    def grates(mx, n):
        lv.hazard(mx, n, grate, A)

    # A: the grand entrance hall
    for px in (6, 16, 26):
        lv.deco(px, 4, pillar(8), A)
    lv.deco(9, 0, chandelier(), B)
    lv.solid(12, 10, mop_bucket(), B)
    lv.deco(14, 10, wet_floor_sign(), B)
    lv.foe(FOE_A, 20, 17, 25)                        # runaway floor buffer
    lv.platform(22, 8, ledge(3), A)
    lv.foe(FOE_C, 24, 21, 28, row=7)                 # bat
    lv.solid(29, 10, stone_block(2, 2), A)
    lv.solid(31, 8, stone_block(2, 4), A)
    lv.heart(32, 7)
    grates(34, 3)
    lv.foe(FOE_B, 41, 38, 45)                        # suit of armor
    # B: the stair tower
    lv.solid(46, 10, stone_block(2, 2), A)
    lv.solid(48, 8, stone_block(2, 4), A)
    lv.solid(50, 6, stone_block(2, 6), A)
    lv.platform(53, 4, ledge(3), A)
    lv.foe(FOE_C, 55, 53, 58, row=4)
    lv.platform(57, 7, ledge(3), A)
    lv.solid(61, 8, stone_block(2, 4), A)
    lv.solid(63, 10, stone_block(2, 2), A)
    lv.foe(FOE_A, 70, 66, 74)
    lv.deco(72, 0, chandelier(), B)
    grates(75, 3)
    lv.deco(80, 4, pillar(8), A)
    lv.platform(83, 9, ledge(3), A)
    lv.platform(87, 7, ledge(3), A)
    lv.heart(88, 6)
    lv.foe(FOE_B, 92, 90, 98)
    # C: the records hall and courtrooms
    lv.platform(100, 10, pew(4), B)
    lv.platform(106, 10, pew(4), B)
    lv.foe(FOE_C, 108, 104, 112, row=8)
    lv.deco(100, 11, carpet(12), B)
    lv.solid(113, 10, mop_bucket(), B)
    lv.foe(FOE_A, 118, 115, 123)
    grates(120, 2)
    lv.solid(124, 10, stone_block(2, 2), A)
    lv.solid(126, 9, judge_bench(), B)
    lv.foe(FOE_B, 134, 131, 139)
    lv.deco(137, 0, chandelier(), B)
    lv.platform(140, 8, ledge(4), A)
    lv.foe(FOE_C, 142, 140, 145, row=8)
    grates(145, 3)
    lv.solid(149, 10, stone_block(2, 2), A)
    lv.deco(152, 10, wet_floor_sign(), B)
    lv.foe(FOE_A, 157, 154, 162)
    lv.platform(161, 9, pew(4), B)
    lv.heart(163, 8)
    lv.foe(FOE_B, 170, 167, 176)
    # D: the grand courtroom (boss arena)
    a0 = LEVEL_W_MT - ARENA_MT
    lv.deco(a0, 4, pillar(8), A)
    lv.deco(LEVEL_W_MT - 2, 4, pillar(8), A)
    lv.platform(a0 + 3, 9, ledge(3), A)
    lv.platform(a0 + 10, 9, ledge(3), A)
    lv.deco(a0 + 6, 0, chandelier(), B)
    lv.start()
    return lv


def backdrop():
    W, H = 512, 224
    c = Canvas(W, H)
    pal = pal_grid(PAL_C)
    for y in range(H):
        for x in range(W):
            course = y // 8
            seam = y % 8 == 7 or (x + (course % 2) * 12) % 24 == 23
            c.set(x, y, 4 if seam else (5 if y % 8 == 0 and noise(x // 24, course, 121) > 0.6 else 3))
    # vaulted arches (period 128) with stained glass windows
    for x0 in range(0, W, 128):
        for y in range(0, 40):                        # vault shadow
            for x in range(x0, x0 + 128):
                d = abs(x - (x0 + 64)) / 64
                if y < 40 - (1 - d * d) * 30:
                    c.set(x, y, 6)
        for y in range(36, 192):                       # pilasters
            for x in range(x0, x0 + 8):
                c.set(x, y, 2 if x - x0 in (0, 1) else 5 if x - x0 < 6 else 4)
        # window: lancet arch, glass in palette D
        wx, wy, ww, wh = x0 + 48, 56, 32, 96
        for y in range(wy, wy + wh):
            for x in range(wx, wx + ww):
                if y < wy + 16:
                    d = abs(x - (wx + ww / 2 - 0.5)) / (ww / 2)
                    if (y - wy) < 16 * (1 - (1 - d) ** 0.5):
                        c.set(x, y, 14 if y % 8 == 7 else 15)   # wall, in palette D
                        continue
                cellx, celly = (x - wx) // 8, (y - wy) // 12
                col = [2, 4, 6, 8, 4, 2, 8, 6][(cellx + celly * 3) % 8]
                if (x - wx) % 8 == 0 or (y - wy) % 12 == 0:
                    col = 10
                elif ((x - wx) % 8 in (1, 2)) and ((y - wy) % 12 in (1, 2)):
                    col += 1
                c.set(x, y, col)
        set_pal_rect(pal, wx, wy, wx + ww, wy + wh, PAL_D)
        # banners between windows
        bx = x0 + 16
        for y in range(48, 120):
            for x in range(bx, bx + 16):
                c.set(x, y, 11 if (x - bx) in (0, 15) else 12 if y > 112 else 11)
        for x in range(bx, bx + 16):
            c.set(x, 48, 13); c.set(x, 49, 13)
        ellipse(c, bx + 8, 74, 4, 4, 13)
        for x in range(bx, bx + 16):                    # notched bottom
            if abs(x - (bx + 7.5)) < 4:
                c.set(x, 119, 14); c.set(x, 118, 14)
        set_pal_rect(pal, bx, 48, bx + 16, 120, PAL_D)
        # wall sconce
        sx = x0 + 104
        fill(c, sx, 120, sx + 4, 132, 8)
        ellipse(c, sx + 2, 116, 2, 4, 9)
    # wainscot of dark wood
    for y in range(176, 224):
        for x in range(W):
            c.set(x, y, 8 if (x % 32 in (0, 31) or y in (176, 177)) else 7)
    return c, pal


def main():
    lv = build_level()
    bg2, bg2pal = backdrop()
    export_stage(5, lv, bg2, bg2pal, (P_STONE, P_JANITOR, P_HALL, P_GLASS), (12, 10, 20))


if __name__ == "__main__":
    main()
