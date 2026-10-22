"""Stage 6: Golden Years. Old friends in a sunny retirement village:
shuffleboard courts, park benches, lawn flamingos, the golf course, the
community pool, the bingo hall, and the boardwalk at sunset where Father
Time makes his final stand.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pixel import Canvas, capsule, ellipse, shade, outlined
from stagekit import (Level, T_EMPTY, T_SOLID, T_PLATE, PAL_A, PAL_B, PAL_C, PAL_D,
                      FOE_A, FOE_B, FOE_C, ARENA_MT, noise, fill, frame_box, export_stage,
                      pal_grid, set_pal_rect)

P_LAWN = [(0, 0, 0), (34, 26, 30),
          (140, 210, 96), (100, 176, 76), (70, 136, 60),          # 2-4 lawn
          (232, 214, 160), (204, 180, 124), (164, 138, 92),       # 5-7 sand / path
          (60, 110, 54), (40, 80, 44),                            # 8-9 hedge
          (180, 160, 120), (140, 110, 80),                        # 10-11 boardwalk
          (80, 180, 220), (170, 230, 250),                        # 12-13 pool water
          (244, 244, 236),                                        # 14 white
          (90, 160, 190)]                                         # 15 pool tile
P_RESORT = [(0, 0, 0), (34, 26, 30),
            (250, 150, 180), (220, 100, 140), (150, 60, 90),      # 2-4 flamingo pink
            (80, 190, 180), (50, 140, 136),                       # 5-6 teal
            (244, 244, 236), (210, 206, 196),                     # 7-8 white
            (190, 130, 80), (140, 92, 56),                        # 9-10 bench wood
            (250, 210, 80),                                       # 11 yellow
            (230, 70, 60),                                        # 12 red
            (60, 100, 180),                                       # 13 blue
            (40, 40, 48),                                         # 14 iron
            (250, 180, 120)]                                      # 15 peach
P_SUNSET = [(0, 0, 0), (40, 24, 50),
            (250, 220, 140), (250, 180, 110), (240, 140, 100),    # 2-4 low sky
            (210, 110, 120), (160, 90, 140), (110, 70, 140),      # 5-7 high sky
            (255, 240, 180),                                      # 8 sun
            (90, 120, 170), (70, 96, 150), (52, 72, 120),         # 9-11 sea
            (250, 200, 150),                                      # 12 sea glint
            (130, 80, 110), (100, 60, 96), (80, 50, 84)]          # 13-15 condo silhouettes
# palms reuse the high-sky indices, which never appear below y=72
P_PALMS = list(P_SUNSET)
P_PALMS[5] = (60, 120, 70)                                        # fronds light
P_PALMS[6] = (40, 90, 56)                                         # fronds dark / trunk ring
P_PALMS[7] = (120, 84, 60)                                        # trunk


def mt_lawn_top():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            n = noise(x, y, 131)
            c.set(x, y, 6 if n < 0.6 else (7 if n < 0.85 else 5))
    for x in range(16):
        depth = 4 + (1 if noise(x, 0, 133) > 0.65 else 0)
        for y in range(depth):
            c.set(x, y, 2 if y == 0 else (3 if y < depth - 1 else 4))
    return c, PAL_A, [T_SOLID] * 4


def mt_sand():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            n = noise(x, y, 135)
            c.set(x, y, 6 if n < 0.5 else (5 if n < 0.85 else 7))
    return c, PAL_A, [T_SOLID] * 4


def mt_boardwalk():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            c.set(x, y, 11 if (x % 8 == 7 or y in (0, 15)) else 10)
    for x in range(16):
        c.set(x, 0, 1)
    c.set(3, 4, 11); c.set(11, 9, 11)
    return c, PAL_A, [T_SOLID] * 4


def shuffleboard(w_mt):
    w = w_mt * 16
    c = Canvas(w, 16)
    for x in range(w):
        for y in range(12, 16):
            c.set(x, y, 13 if y == 12 else 15)
    for x0 in range(8, w, 32):
        for y in range(13, 16):
            c.set(x0, y, 14); c.set(x0 + 1, y, 14)
    return c


def hedge(w_mt):
    w = w_mt * 16
    c = Canvas(w, 32)
    fill(c, 1, 6, w - 1, 32, 8)
    for x in range(1, w - 1):
        top = 4 + int(noise(x // 3, 0, 137) * 3)
        for y in range(top, 8):
            c.set(x, y, 8)
    for y in range(6, 32):
        for x in range(1, w - 1):
            if noise(x, y, 139) > 0.75:
                c.set(x, y, 9)
            elif noise(x, y, 141) > 0.85:
                c.set(x, y, 3)
    return outlined(c, 1)


def bench():
    c = Canvas(32, 32)
    fill(c, 2, 14, 30, 18, 9)                        # seat slats
    fill(c, 2, 4, 30, 7, 9)                          # back slats
    fill(c, 2, 8, 30, 11, 10)
    for x in (4, 27):
        capsule(c, (x, 4), (x, 31), 0.8, 14)
    capsule(c, (4, 18), (8, 31), 0.6, 14)
    capsule(c, (27, 18), (23, 31), 0.6, 14)
    return outlined(c, 1)


def flamingo():
    c = Canvas(16, 32)
    ellipse(c, 7, 14, 5, 3.5, 2)
    capsule(c, (10, 13), (11, 5), 0.9, 2)
    ellipse(c, 11, 4, 2, 1.8, 2)
    c.set(13, 4, 14); c.set(14, 5, 14)
    capsule(c, (7, 17), (7, 31), 0.5, 14)
    shade(c, 2, None, 3)
    return outlined(c, 1)


def umbrella_table():
    c = Canvas(48, 48)
    for x in range(48):
        d = abs(x - 23.5)
        top = 4 + int(d * d / 70)
        for y in range(top, 14):
            c.set(x, y, 12 if (x // 6) % 2 else 7)
    capsule(c, (24, 4), (24, 46), 0.6, 14)
    fill(c, 10, 34, 38, 37, 7)                       # table top
    capsule(c, (14, 37), (14, 47), 0.5, 14)
    capsule(c, (34, 37), (34, 47), 0.5, 14)
    return outlined(c, 1)


def condo_balcony(w_mt):
    w = w_mt * 16
    c = Canvas(w, 16)
    fill(c, 0, 0, w, 4, 7)
    for x in range(w):
        c.set(x, 0, 1); c.set(x, 3, 8)
        if x % 4 == 0:
            for y in range(4, 14):
                c.set(x, y, 5)
        c.set(x, 13, 5)
    return c


def condo_wall(w_mt, h_mt):
    w, h = w_mt * 16, h_mt * 16
    c = Canvas(w, h)
    fill(c, 0, 0, w, h, 15)
    for wy in range(6, h - 10, 32):
        for wx in range(6, w - 12, 20):
            fill(c, wx, wy, wx + 12, wy + 14, 13)
            fill(c, wx + 1, wy + 1, wx + 11, wy + 13, 5)
            for x in range(wx, wx + 12):
                c.set(x, wy + 14, 8)
    frame_box(c, 0, 0, w, h, 1)
    return c


def golf_flag():
    c = Canvas(16, 48)
    capsule(c, (4, 2), (4, 46), 0.5, 7)
    for y in range(2, 12):
        for x in range(5, 5 + (12 - y) + 2):
            c.set(x, y, 11 if y > 3 else 12)
    for y in range(2, 12):
        for x in range(5, 14 - abs(y - 7)):
            c.set(x, y, 12)
    return outlined(c, 1)


def bingo_table(w_mt):
    w = w_mt * 16
    c = Canvas(w, 32)
    fill(c, 0, 2, w, 7, 7)
    for x in range(w):
        c.set(x, 2, 8); c.set(x, 6, 8)
    for x0 in range(4, w - 8, 12):                   # bingo cards
        fill(c, x0, 0, x0 + 8, 3, 11)
    for x in (3, w - 4):
        capsule(c, (x, 7), (x, 31), 0.6, 14)
    return outlined(c, 1)


def pool(part):
    c = Canvas(16, 32)
    fill(c, 0, 4, 16, 28, 12)
    for y in range(4, 28):
        for x in range(16):
            if (x + y * 2) % 8 == 0 or (y < 7 and x % 5 == 2):
                c.set(x, y, 13)
    for x in range(16):
        c.set(x, 3, 14); c.set(x, 4, 15)
    fill(c, 0, 28, 16, 32, 15)
    if part == 0:
        fill(c, 0, 0, 2, 28, 14); c.set(1, 0, 1)
        capsule(c, (4, 0), (4, 10), 0.5, 14)            # pool ladder
        capsule(c, (7, 0), (7, 10), 0.5, 14)
    if part == 2:
        fill(c, 14, 0, 16, 28, 14)
    return c


LEVEL_W_MT = 200


def build_level():
    lv = Level(LEVEL_W_MT)
    lawn, sand, board = mt_lawn_top(), mt_sand(), mt_boardwalk()
    lv.floor(lawn, sand)
    A, B = PAL_A, PAL_B
    for mx in range(LEVEL_W_MT - ARENA_MT - 8, LEVEL_W_MT):
        lv.put(mx, 12, board, merge=False)

    def pools(mx, n):
        lv.hazard(mx, n, pool, A)

    # A: shuffleboard courts and the park
    lv.deco(4, 11, shuffleboard(8), A)
    lv.platform(13, 10, bench(), B)
    lv.foe(FOE_B, 19, 16, 23)                        # goose
    lv.deco(22, 10, flamingo(), B)
    lv.solid(25, 10, hedge(3), A)
    lv.foe(FOE_C, 30, 28, 34)                        # bingo ball
    lv.deco(34, 9, umbrella_table(), B)
    lv.platform(38, 10, bench(), B)
    lv.heart(39, 9)
    pools(42, 4)
    lv.foe(FOE_A, 50, 47, 56)                        # golf cart
    # B: the condos
    lv.deco(56, 2, condo_wall(10, 10), B)
    lv.platform(56, 9, condo_balcony(4), B)
    lv.platform(61, 7, condo_balcony(4), B)
    lv.platform(56, 5, condo_balcony(4), B)
    lv.foe(FOE_C, 58, 56, 60, row=5)
    lv.heart(58, 4)
    lv.platform(62, 3, condo_balcony(3), B)
    lv.foe(FOE_B, 66, 63, 70)
    lv.solid(70, 10, hedge(2), A)
    lv.solid(73, 10, hedge(2), A)
    lv.solid(73, 8, hedge(2), A)
    pools(76, 3)
    lv.deco(80, 11, shuffleboard(6), A)
    lv.foe(FOE_A, 85, 81, 90)
    # C: the golf course
    lv.deco(92, 9, golf_flag(), B)
    lv.platform(95, 9, bench(), B)
    lv.foe(FOE_C, 99, 97, 104)
    pools(103, 9)                                    # the lazy river: ride a raft
    lv.raft(103, 112)
    lv.solid(113, 10, hedge(3), A)
    lv.foe(FOE_B, 118, 116, 121)
    lv.deco(118, 10, flamingo(), B)
    lv.deco(120, 10, flamingo(), B)
    lv.foe(FOE_A, 126, 122, 131)
    # D: the bingo hall
    lv.platform(132, 10, bingo_table(4), B)
    lv.foe(FOE_C, 134, 132, 136, row=10)
    lv.platform(138, 8, bingo_table(4), B)
    lv.platform(144, 10, bingo_table(4), B)
    lv.foe(FOE_C, 146, 144, 148, row=10)
    lv.heart(140, 7)
    pools(149, 9)                                    # the big pool
    lv.raft(149, 158)
    lv.foe(FOE_B, 161, 159, 164)
    lv.deco(158, 9, umbrella_table(), B)
    lv.foe(FOE_A, 166, 162, 170)
    lv.platform(170, 9, bench(), B)
    lv.foe(FOE_C, 172, 170, 175)
    # E: the boardwalk at sunset (boss arena)
    a0 = LEVEL_W_MT - ARENA_MT
    lv.platform(a0 + 3, 9, condo_balcony(3), B)
    lv.platform(a0 + 10, 9, condo_balcony(3), B)
    lv.start()
    return lv


def backdrop():
    W, H = 512, 224
    c = Canvas(W, H)
    pal = pal_grid(PAL_C)
    bands = [(0, 7), (24, 6), (48, 5), (72, 4), (96, 3), (112, 2)]
    for y in range(H):
        col = 7
        for (y0, cc) in bands:
            if y >= y0:
                col = cc
        for x in range(W):
            # dithered band edges for a smoother gradient
            if y % 24 < 2 and (x + y) % 2 == 0 and y > 2 and y < 120:
                c.set(x, y, col + 1 if col < 7 else col)
            else:
                c.set(x, y, col)
    ellipse(c, 256, 128, 26, 26, 8)                  # setting sun
    for y in range(128, 160):
        for x in range(W):
            c.set(x, y, 9 if y < 136 else (10 if y < 148 else 11))
    for y in range(128, 160, 3):                      # sun glints on the sea
        for x in range(236, 278, 5):
            if noise(x, y, 151) > 0.3:
                c.set(x + (y % 2), y, 12)
    # condo silhouettes (period 256)
    for x0 in range(0, W, 256):
        bx, k = x0, 0
        while bx < x0 + 256:
            bw = 30 + int(noise(k, x0, 153) * 30)
            bh = 30 + int(noise(k, x0, 155) * 40)
            if not (200 < bx < 300 and x0 == 0):
                fill(c, bx, 160 - bh, bx + bw, 224, 13 + (k % 3))
                for wy in range(160 - bh + 5, 158, 8):
                    for wx in range(bx + 3, bx + bw - 3, 6):
                        if noise(wx, wy, 157) > 0.6:
                            fill(c, wx, wy, wx + 2, wy + 3, 2)
            bx += bw + 18
            k += 1
    fill(c, 0, 176, W, 224, 15)
    # palm trees in palette D
    for x0 in range(24, W, 96):
        tx = x0
        for y in range(100, 216):
            sway = int(math.sin((216 - y) / 40) * 6)
            fill(c, tx + sway, y, tx + sway + 4, y + 1, 7 if y % 6 else 6)
        top = tx + int(math.sin(116 / 40) * 6) + 2
        for a in range(7):
            ang = -math.pi + a * math.pi / 6
            for t in range(28):
                px = top + math.cos(ang) * t
                py = 100 + math.sin(ang) * t * 0.5 + (t * t) / 40
                capsule(c, (px, py), (px, py + 1.5), 1.0, 5 if t < 18 else 6)
        set_pal_rect(pal, tx - 32, 80, tx + 40, 216, PAL_D)
    return c, pal


def main():
    lv = build_level()
    bg2, bg2pal = backdrop()
    export_stage(6, lv, bg2, bg2pal, (P_LAWN, P_RESORT, P_SUNSET, P_PALMS), (110, 70, 140))


if __name__ == "__main__":
    main()
