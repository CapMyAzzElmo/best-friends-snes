"""Stage 4: Chicago Fest. A music festival weekend in the city: park lawns,
food trucks, barricades, port-a-potties, the elevated train tracks, the
green-dyed river, and the main festival stage where the Pigeon King rules
the skies.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pixel import Canvas, capsule, ellipse, shade, outlined
from stagekit import (Level, T_EMPTY, T_SOLID, T_PLATE, PAL_A, PAL_B, PAL_C, PAL_D,
                      FOE_A, FOE_B, FOE_C, ARENA_MT, noise, fill, frame_box, export_stage,
                      pal_grid, set_pal_rect)

P_PARK = [(0, 0, 0), (20, 24, 30),
          (120, 196, 84), (84, 160, 64), (56, 118, 48),           # 2-4 grass
          (150, 112, 74), (110, 80, 54),                          # 5-6 soil
          (176, 176, 168), (138, 138, 132), (100, 100, 98),       # 7-9 pavement
          (78, 104, 92), (54, 74, 66),                            # 10-11 el girder green
          (60, 170, 110), (130, 220, 160),                        # 12-13 green river
          (240, 240, 232),                                        # 14 white
          (220, 70, 56)]                                          # 15 red
P_FEST = [(0, 0, 0), (20, 24, 30),
          (240, 240, 232), (200, 200, 196),                       # 2-3 truck white
          (220, 70, 56), (160, 44, 40),                           # 4-5 red
          (70, 130, 210), (46, 90, 160),                          # 6-7 blue
          (250, 200, 70), (200, 140, 40),                         # 8-9 mustard
          (80, 80, 90), (50, 50, 60),                             # 10-11 scaffold
          (150, 210, 240),                                        # 12 window
          (240, 170, 120),                                        # 13 bun
          (130, 70, 50),                                          # 14 sausage
          (60, 160, 80)]                                          # 15 relish
P_SKY = [(0, 0, 0), (40, 52, 80),
         (150, 200, 250), (126, 180, 240), (104, 160, 230),       # 2-4 sky
         (250, 250, 255), (210, 226, 246),                        # 5-6 clouds
         (120, 140, 170), (96, 112, 142), (74, 86, 114),          # 7-9 far towers
         (56, 62, 80), (36, 40, 54),                              # 10-11 near towers / Willis
         (200, 220, 240),                                         # 12 glass glint
         (70, 120, 170), (46, 90, 140),                           # 13-14 lake
         (230, 238, 250)]                                         # 15
# shares the sky/city colours with P_SKY at the same indices so tree and flag
# tiles can sit over the skyline
P_TREES = list(P_SKY)
P_TREES[3] = (200, 60, 50)                                    # flag red
P_TREES[4] = (240, 240, 232)                                  # flag white
P_TREES[5] = (110, 80, 60)                                    # trunk
P_TREES[12] = (110, 180, 80)                                  # leaves light
P_TREES[13] = (70, 136, 60)                                   # leaves mid
P_TREES[14] = (44, 96, 46)                                    # leaves dark
P_TREES[15] = (60, 110, 190)                                  # flag blue


def mt_grass_top():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            n = noise(x, y, 91)
            c.set(x, y, 5 if n < 0.6 else 6)
    for x in range(16):
        depth = 4 + (1 if noise(x, 0, 93) > 0.6 else 0)
        for y in range(depth):
            c.set(x, y, 2 if y == 0 else (3 if y < depth - 1 else 4))
        if noise(x, 3, 95) > 0.7:
            c.set(x, depth, 4)
    return c, PAL_A, [T_SOLID] * 4


def mt_soil():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            n = noise(x, y, 97)
            c.set(x, y, 6 if n < 0.55 else (5 if n < 0.9 else 9))
    return c, PAL_A, [T_SOLID] * 4


def mt_pavement_top():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            c.set(x, y, 8 if noise(x, y, 99) < 0.8 else 9)
    for x in range(16):
        c.set(x, 0, 1); c.set(x, 1, 7); c.set(x, 2, 7)
    for y in range(3, 16):
        c.set(0, y, 9)
    return c, PAL_A, [T_SOLID] * 4


def food_truck():
    c = Canvas(64, 48)
    fill(c, 2, 4, 62, 40, 2)
    fill(c, 2, 4, 62, 8, 4)                          # red roof stripe
    fill(c, 10, 12, 44, 26, 12)                      # service window
    frame_box(c, 10, 12, 44, 26, 3)
    fill(c, 8, 26, 46, 29, 9)                        # counter ledge
    # hot dog on the side
    capsule(c, (14, 34), (40, 34), 2.6, 13)
    capsule(c, (16, 33), (38, 33), 1.4, 14)
    for x in range(17, 38, 4):
        c.set(x, 32, 8)
    fill(c, 48, 10, 60, 24, 12)                      # cab window
    fill(c, 2, 36, 62, 40, 3)
    for wx in (14, 50):
        ellipse(c, wx, 41, 5, 5, 11)
        ellipse(c, wx, 41, 2, 2, 3)
    o = outlined(c, 1)
    return o


def barricade(w_mt):
    w = w_mt * 16
    c = Canvas(w, 16)
    for x in range(w):
        c.set(x, 2, 2); c.set(x, 3, 3)
        c.set(x, 8, 2); c.set(x, 9, 3)
    for x in range(0, w, 4):
        for y in range(2, 10):
            c.set(x, y, 3)
    for x in (1, w - 2):
        for y in range(2, 16):
            c.set(x, y, 10)
    return outlined(c, 1)


def porta_potty():
    c = Canvas(32, 48)
    fill(c, 3, 6, 29, 46, 6)
    ellipse(c, 16, 6, 14, 5, 7)
    fill(c, 7, 12, 25, 44, 7)                        # door
    fill(c, 20, 26, 23, 30, 2)                       # handle / sign
    fill(c, 10, 15, 22, 18, 4)                       # occupied!
    for y in range(8, 46, 4):
        c.set(4, y, 7); c.set(27, y, 7)
    return outlined(c, 1)


def el_track(w_mt):
    """Elevated train girder deck: one-way on top."""
    w = w_mt * 16
    c = Canvas(w, 16)
    for x in range(w):
        c.set(x, 0, 1); c.set(x, 1, 10); c.set(x, 2, 10); c.set(x, 3, 11)
        c.set(x, 10, 10); c.set(x, 11, 11)
        if x % 8 < 4:                               # lattice
            c.set(x, 4 + (x % 8) * 2 // 1 if 4 + (x % 8) * 2 < 10 else 9, 10)
        else:
            c.set(x, 4 + (7 - x % 8) * 2 if 4 + (7 - x % 8) * 2 < 10 else 9, 10)
    return c


def el_pillar(h_mt):
    c = Canvas(16, h_mt * 16)
    fill(c, 4, 0, 12, c.h, 10)
    for y in range(c.h):
        c.set(4, y, 11); c.set(11, y, 11)
        if y % 12 == 0:
            for x in range(3, 13):
                c.set(x, y, 11)
    return outlined(c, 1)


def scaffold(w_mt, h_mt):
    w, h = w_mt * 16, h_mt * 16
    c = Canvas(w, h)
    for x in (1, w - 2):
        capsule(c, (x, 0), (x, h - 1), 0.6, 10)
    for y in range(0, h, 16):
        capsule(c, (0, y + 1), (w - 1, y + 1), 0.6, 10)
        capsule(c, (1, y + 1), (w - 2, y + 15), 0.4, 11)
    return c


def stage_deck(w_mt):
    w = w_mt * 16
    c = Canvas(w, 16)
    fill(c, 0, 0, w, 6, 11)
    for x in range(w):
        c.set(x, 0, 1); c.set(x, 1, 10)
    fill(c, 0, 6, w, 16, 10)
    for x in range(0, w, 6):
        for y in range(6, 16):
            c.set(x, y, 11)
    return c


def river(part):
    c = Canvas(16, 32)
    fill(c, 0, 6, 16, 28, 12)
    for y in range(6, 28):
        for x in range(16):
            if (x + y * 2) % 9 == 0 or (y < 9 and x % 4 == 1):
                c.set(x, y, 13)
    for x in range(16):
        c.set(x, 5, 1)
    fill(c, 0, 28, 16, 32, 6)
    if part == 0:
        fill(c, 0, 0, 3, 28, 8); fill(c, 0, 0, 1, 28, 1)
    if part == 2:
        fill(c, 13, 0, 16, 28, 8); fill(c, 15, 0, 16, 28, 1)
    return c


def bench_crates():
    """Stacked speaker road cases."""
    c = Canvas(32, 32)
    for (x0, y0) in ((0, 16), (16, 16), (0, 0)):
        fill(c, x0 + 1, y0 + 1, x0 + 15, y0 + 15, 11)
        frame_box(c, x0 + 1, y0 + 1, x0 + 15, y0 + 15, 10)
        for (x, y) in ((x0 + 2, y0 + 2), (x0 + 13, y0 + 2), (x0 + 2, y0 + 13), (x0 + 13, y0 + 13)):
            c.set(x, y, 3)
    return outlined(c, 1)


LEVEL_W_MT = 196


def build_level():
    lv = Level(LEVEL_W_MT)
    grass, soil, pave = mt_grass_top(), mt_soil(), mt_pavement_top()
    lv.floor(grass, soil)
    A, B = PAL_A, PAL_B
    for mx in range(60, 120):                          # downtown stretch is paved
        lv.put(mx, 12, pave, merge=False)

    def rivers(mx, n):
        lv.hazard(mx, n, river, A)

    # A: the festival lawn
    lv.solid(6, 11, barricade(2), B)                 # steps up onto the tall props
    lv.solid(8, 9, food_truck(), B)
    lv.foe(FOE_A, 16, 13, 22)                        # security guard
    lv.solid(22, 11, barricade(3), B)
    lv.foe(FOE_C, 27, 24, 32, row=8)                 # pigeon
    lv.solid(28, 10, bench_crates(), B)
    lv.solid(30, 9, porta_potty(), B)
    lv.solid(32, 9, porta_potty(), B)
    lv.heart(33, 7)
    lv.foe(FOE_B, 38, 35, 44)                        # hot dog mascot
    rivers(44, 3)
    lv.solid(48, 10, bench_crates(), B)
    lv.solid(50, 10, bench_crates(), B)
    lv.solid(50, 8, bench_crates(), B)
    lv.foe(FOE_A, 56, 53, 60)
    # B: under the L tracks downtown
    for px in (62, 72, 82, 92, 102):
        lv.deco(px, 6, el_pillar(6), A)
    lv.platform(60, 5, el_track(46), A)
    lv.solid(64, 11, barricade(3), B)
    lv.foe(FOE_C, 68, 64, 72, row=5)
    lv.solid(68, 11, barricade(2), B)
    lv.solid(70, 9, food_truck(), B)
    lv.foe(FOE_B, 78, 75, 84)
    lv.heart(80, 4)
    rivers(85, 3)
    lv.solid(89, 11, barricade(2), B)
    lv.foe(FOE_A, 95, 91, 100)
    lv.foe(FOE_C, 98, 94, 104, row=5)
    lv.solid(104, 10, bench_crates(), B)
    lv.foe(FOE_B, 112, 108, 117)
    rivers(117, 4)
    # C: the river walk and back stage
    lv.platform(121, 9, stage_deck(3), B)
    lv.deco(121, 10, scaffold(3, 2), B)
    lv.platform(126, 7, stage_deck(3), B)
    lv.deco(126, 8, scaffold(3, 4), B)
    lv.foe(FOE_C, 128, 126, 129, row=7)
    lv.platform(131, 9, stage_deck(3), B)
    lv.deco(131, 10, scaffold(3, 2), B)
    lv.foe(FOE_A, 137, 134, 142)
    lv.solid(140, 11, barricade(2), B)
    lv.solid(142, 9, porta_potty(), B)
    rivers(145, 3)
    lv.solid(149, 10, bench_crates(), B)
    lv.foe(FOE_B, 155, 152, 160)
    lv.solid(160, 11, barricade(3), B)
    lv.foe(FOE_C, 165, 162, 170, row=8)
    lv.heart(170, 9)
    lv.foe(FOE_A, 174, 171, 178)
    # D: the main stage (boss arena)
    a0 = LEVEL_W_MT - ARENA_MT
    lv.platform(a0 + 2, 9, stage_deck(4), B)
    lv.deco(a0 + 2, 10, scaffold(4, 2), B)
    lv.platform(a0 + 10, 9, stage_deck(4), B)
    lv.deco(a0 + 10, 10, scaffold(4, 2), B)
    lv.start()
    return lv


def backdrop():
    W, H = 512, 224
    c = Canvas(W, H)
    pal = pal_grid(PAL_C)
    for y in range(H):
        col = 4 if y < 40 else (3 if y < 90 else 2)
        for x in range(W):
            c.set(x, y, col)
    for (cx, cy, s) in ((60, 30, 1.0), (230, 50, 0.7), (380, 24, 1.2)):   # clouds
        for (dx, dy, r) in ((0, 0, 12), (14, 2, 10), (-13, 3, 9), (6, -6, 9)):
            ellipse(c, cx + dx * s, cy + dy * s, r * s * 1.3, r * s * 0.7, 6)
        for (dx, dy, r) in ((0, -1, 10), (12, 0, 8), (-11, 1, 7)):
            ellipse(c, cx + dx * s, cy + dy * s - 2, r * s * 1.2, r * s * 0.6, 5)
    # far skyline (period 256)
    for x0 in range(0, W, 256):
        bx, k = x0, 0
        while bx < x0 + 256:
            bw = 16 + int(noise(k, x0, 101) * 22)
            bh = 40 + int(noise(k, x0, 103) * 50)
            fill(c, bx, 170 - bh, bx + bw, 224, 7)
            for wy in range(170 - bh + 4, 168, 6):
                for wx in range(bx + 2, bx + bw - 2, 4):
                    c.set(wx, wy, 6)
            bx += bw + 1
            k += 1
    # the big towers: Willis (stepped, twin antennas) and Hancock (tapered, X braces)
    def willis(x):
        for (dx, w, top) in ((0, 28, 48), (6, 18, 34), (10, 12, 26)):
            fill(c, x + dx, top, x + dx + w, 224, 11)
        for (ax) in (x + 12, x + 19):
            fill(c, ax, 8, ax + 1, 26, 10)
        for y in range(52, 200, 5):
            for wx in range(x + 2, x + 26, 3):
                c.set(wx, y, 10)

    def hancock(x):
        for y in range(40, 224):
            inset = (y - 40) // 20
            fill(c, x + 6 - min(inset, 6), y, x + 22 + min(inset, 6), y + 1, 10)
        for y0 in range(48, 200, 24):
            for i in range(20):
                c.set(x + 6 + i * 16 // 20, y0 + i, 9)
                c.set(x + 22 - i * 16 // 20, y0 + i, 9)
        fill(c, x + 10, 14, x + 11, 40, 10)
        fill(c, x + 17, 18, x + 18, 40, 10)
    willis(100)
    hancock(330)
    fill(c, 0, 172, W, 224, 9)                       # mid city band
    for x in range(0, W, 6):
        for y in range(176, 224, 6):
            c.set(x + 2, y, 8)
    # park trees and festival flags in the foreground (palette D)
    for x0 in range(16, W, 64):
        trunk = x0 + 8
        fill(c, trunk, 176, trunk + 3, 216, 5)
        for (dx, dy, r) in ((0, 0, 14), (-10, 8, 10), (10, 8, 10), (0, 14, 12)):
            ellipse(c, trunk + 1 + dx, 172 + dy, r, r * 0.8, 14)
        for (dx, dy, r) in ((0, -2, 11), (-8, 5, 7), (8, 5, 7)):
            ellipse(c, trunk + 1 + dx, 171 + dy, r, r * 0.75, 13)
        for (dx, dy, r) in ((-3, -4, 7), (6, 1, 5)):
            ellipse(c, trunk + 1 + dx, 169 + dy, r, r * 0.8, 12)
        set_pal_rect(pal, trunk - 16, 152, trunk + 24, 224, PAL_D)
    for x0 in range(48, W, 64):                      # banner string with flags
        for i in range(4):
            fx = x0 + i * 4
            col = [3, 4, 15, 4][i]
            fill(c, fx, 150 + (i % 2), fx + 3, 156 + (i % 2), col)
        set_pal_rect(pal, x0, 144, x0 + 16, 160, PAL_D)
    return c, pal


def main():
    lv = build_level()
    bg2, bg2pal = backdrop()
    export_stage(4, lv, bg2, bg2pal, (P_PARK, P_FEST, P_SKY, P_TREES), (150, 200, 250))


if __name__ == "__main__":
    main()
