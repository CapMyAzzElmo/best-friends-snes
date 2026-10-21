"""Stage 3: Bar Town Nights. Stumbling down a college bar town street after
dark with punk bands blasting: sidewalks, dumpsters, awnings, fire escapes,
open storm drains, a dive bar counter, and the punk club stage where the
Bouncer guards the door.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pixel import Canvas, capsule, ellipse, shade, outlined
from stagekit import (Level, T_EMPTY, T_SOLID, T_PLATE, PAL_A, PAL_B, PAL_C, PAL_D,
                      FOE_A, FOE_B, FOE_C, ARENA_MT, noise, fill, frame_box, export_stage,
                      pal_grid, set_pal_rect)

P_STREET = [(0, 0, 0), (16, 14, 24),
            (150, 150, 160), (116, 116, 128), (84, 84, 98),       # 2-4 concrete
            (150, 70, 56), (112, 50, 44), (76, 34, 34),           # 5-7 brick
            (60, 110, 70), (40, 76, 50),                          # 8-9 dumpster green
            (180, 180, 190),                                      # 10 steel
            (90, 90, 104),                                        # 11 dark steel
            (60, 120, 170),                                       # 12 drain water
            (120, 190, 230),                                      # 13 water glint
            (230, 200, 90),                                       # 14 yellow paint
            (240, 240, 230)]                                      # 15 white
P_NEON = [(0, 0, 0), (16, 14, 24),
          (240, 80, 150), (170, 40, 100),                         # 2-3 neon pink
          (90, 220, 240), (40, 140, 180),                         # 4-5 neon cyan
          (200, 60, 50), (140, 36, 34),                           # 6-7 awning red
          (240, 230, 220),                                        # 8 awning white
          (92, 56, 40), (132, 84, 54), (176, 120, 76),            # 9-11 bar wood
          (220, 170, 60),                                         # 12 beer gold
          (250, 240, 200),                                        # 13 foam
          (60, 60, 70),                                           # 14 stool
          (34, 30, 40)]                                           # 15 shadow
P_NIGHT = [(0, 0, 0), (10, 10, 22),
           (22, 24, 52), (32, 36, 72), (46, 52, 96),              # 2-4 sky bands
           (30, 26, 40), (44, 38, 56), (58, 50, 72),              # 5-7 buildings
           (250, 214, 120), (200, 150, 80),                       # 8-9 lit windows
           (230, 230, 250),                                       # 10 stars/moon
           (70, 64, 90),                                          # 11 roof edge
           (20, 18, 30),                                          # 12 dark windows
           (130, 120, 160),                                       # 13 moon shade
           (88, 80, 110), (36, 32, 48)]                           # 14-15
P_SIGNS = [(0, 0, 0), (10, 10, 22),
           (255, 90, 160), (255, 170, 210),                       # 2-3 pink
           (90, 230, 250), (190, 250, 255),                       # 4-5 cyan
           (255, 210, 80), (255, 240, 170),                       # 6-7 yellow
           (120, 250, 120), (200, 255, 200),                      # 8-9 green
           (40, 36, 52), (60, 54, 76),                            # 10-11 sign box
           (230, 230, 250),                                       # 12 lamp
           (90, 80, 110),                                         # 13 pole
           (250, 214, 120), (44, 38, 56)]                         # 14-15


def mt_sidewalk_top():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            n = noise(x, y, 61)
            c.set(x, y, 3 if n < 0.7 else (2 if n < 0.85 else 4))
    for x in range(16):
        c.set(x, 0, 1); c.set(x, 1, 2); c.set(x, 2, 2)
        c.set(x, 11, 4); c.set(x, 12, 4)               # curb line
    for y in range(3, 11):
        c.set(15, y, 4)                                 # slab joint
    return c, PAL_A, [T_SOLID] * 4


def mt_street():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            n = noise(x, y, 63)
            c.set(x, y, 4 if n < 0.75 else (11 if n < 0.9 else 3))
    for x in range(4, 12):
        c.set(x, 8, 14); c.set(x, 9, 14)               # lane paint
    return c, PAL_A, [T_SOLID] * 4


def dumpster():
    c = Canvas(48, 32)
    fill(c, 1, 4, 47, 30, 8)
    fill(c, 0, 2, 48, 6, 9)                            # lid
    for x in range(4, 46, 6):
        for y in range(8, 28):
            c.set(x, y, 9)
    fill(c, 8, 14, 20, 18, 10)                          # label plate
    for x in (5, 42):
        ellipse(c, x, 30, 2, 2, 11)
    o = outlined(c, 1)
    frame_box(o, 0, 2, 48, 32, 1)
    return o


def trash_can():
    c = Canvas(16, 32)
    fill(c, 2, 8, 14, 32, 10)
    for x in (4, 7, 10):
        for y in range(10, 31):
            c.set(x, y, 11)
    fill(c, 1, 5, 15, 9, 11)
    fill(c, 6, 3, 10, 5, 11)
    return outlined(c, 1)


def awning(w_mt):
    w = w_mt * 16
    c = Canvas(w, 16)
    for x in range(w):
        col = 6 if (x // 8) % 2 == 0 else 8
        for y in range(0, 10):
            c.set(x, y, col)
        if (x % 8) in (2, 3, 4, 5):                     # scalloped edge
            c.set(x, 10, col); c.set(x, 11, col)
        c.set(x, 0, 7)
    o = outlined(c, 1)
    return o


def fire_escape(w_mt):
    w = w_mt * 16
    c = Canvas(w, 16)
    for x in range(w):
        c.set(x, 0, 1); c.set(x, 1, 10); c.set(x, 2, 11); c.set(x, 3, 1)
        if x % 4 == 0:
            for y in range(4, 12):
                c.set(x, y, 11)
        c.set(x, 8, 10)
    return c


def brick_wall(w_mt, h_mt, window=True):
    w, h = w_mt * 16, h_mt * 16
    c = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            course = y // 4
            seam = y % 4 == 3 or (x + (course % 2) * 4) % 8 == 7
            c.set(x, y, 7 if seam else (5 if noise(x // 8, course, 71) > 0.7 else 6))
    if window:
        for wy in range(8, h - 8, 32):
            for wx in range(8, w - 16, 24):
                fill(c, wx, wy, wx + 12, wy + 16, 1)
                fill(c, wx + 1, wy + 1, wx + 11, wy + 15, 12 if noise(wx, wy, 73) > 0.4 else 11)
                for x in range(wx, wx + 12):
                    c.set(x, wy + 16, 3)
    frame_box(c, 0, 0, w, h, 1)
    return c


def bar_counter(w_mt):
    """Dive bar counter: top is a one-way platform."""
    w = w_mt * 16
    c = Canvas(w, 32)
    fill(c, 0, 0, w, 5, 11)
    for x in range(w):
        c.set(x, 0, 1); c.set(x, 1, 11); c.set(x, 4, 9)
    fill(c, 2, 5, w - 2, 32, 10)
    for x0 in range(6, w - 8, 16):                     # panels
        frame_box(c, x0, 9, x0 + 12, 28, 9)
    for x in range(w):
        c.set(x, 30, 9); c.set(x, 31, 1)
    return c


def stool():
    c = Canvas(16, 32)
    ellipse(c, 8, 16, 6, 2, 14)
    capsule(c, (8, 17), (8, 31), 0.8, 14)
    capsule(c, (4, 26), (12, 26), 0.5, 14)
    return outlined(c, 1)


def beer_mugs():
    c = Canvas(16, 16)
    for mx in (2, 9):
        fill(c, mx, 6, mx + 5, 15, 12)
        fill(c, mx, 4, mx + 5, 7, 13)
        c.set(mx + 5, 9, 12); c.set(mx + 6, 10, 12); c.set(mx + 5, 11, 12)
    return outlined(c, 1)


def storm_drain(part):
    c = Canvas(16, 32)
    fill(c, 0, 4, 16, 28, 12)
    for y in range(4, 28):
        for x in range(16):
            if (x * 3 + y) % 11 == 0:
                c.set(x, y, 13)
    for x in range(16):
        c.set(x, 3, 1); c.set(x, 4, 13)
    fill(c, 0, 28, 16, 32, 4)
    if part == 0:
        fill(c, 0, 0, 2, 28, 3)
    if part == 2:
        fill(c, 14, 0, 16, 28, 3)
    return c


def crate_stack():
    c = Canvas(32, 32)
    for (x0, y0) in ((0, 16), (16, 16), (8, 0)):
        fill(c, x0 + 1, y0 + 1, x0 + 15, y0 + 15, 10)
        frame_box(c, x0 + 1, y0 + 1, x0 + 15, y0 + 15, 9)
        for x in range(x0 + 3, x0 + 14, 3):
            c.set(x, y0 + 3, 12); c.set(x, y0 + 4, 12)
    return outlined(c, 1)


def neon_sign(text_kind):
    c = Canvas(32, 16)
    fill(c, 0, 0, 32, 16, 15)
    frame_box(c, 0, 0, 32, 16, 1)
    if text_kind == 0:          # a beer mug outline
        frame_box(c, 10, 3, 19, 13, 2)
        capsule(c, (19, 5), (22, 8), 0.5, 2)
        capsule(c, (22, 8), (19, 11), 0.5, 2)
        for x in range(10, 19, 2):
            c.set(x, 2, 4)
    else:                       # lightning bolt (punk)
        pts = [(18, 2), (12, 8), (17, 8), (13, 14)]
        for a, b in zip(pts, pts[1:]):
            capsule(c, a, b, 0.6, 4)
    return c


LEVEL_W_MT = 192


def build_level():
    lv = Level(LEVEL_W_MT)
    lv.floor(mt_sidewalk_top(), mt_street())
    A, B = PAL_A, PAL_B

    def drains(mx, n):
        lv.hazard(mx, n, storm_drain, A)

    # A: main street
    lv.solid(10, 10, dumpster(), A)
    lv.solid(14, 10, trash_can(), A)
    lv.platform(17, 7, awning(4), B)
    lv.deco(17, 8, neon_sign(0), B)
    lv.foe(FOE_A, 23, 20, 29)                       # punk
    drains(29, 2)
    lv.solid(32, 10, crate_stack(), A)
    lv.foe(FOE_C, 36, 34, 40)                       # rat
    lv.deco(40, 4, brick_wall(6, 8), A)
    lv.platform(40, 6, fire_escape(6), A)
    lv.platform(41, 9, fire_escape(4), A)
    lv.heart(43, 5)
    lv.foe(FOE_B, 44, 41, 48)                       # frat bro
    drains(48, 3)
    lv.solid(52, 10, trash_can(), A)
    lv.platform(54, 8, awning(5), B)
    lv.deco(55, 9, neon_sign(1), B)
    lv.foe(FOE_A, 60, 57, 66)
    # B: inside the dive bar
    lv.deco(68, 2, brick_wall(2, 10, window=False), A)
    lv.platform(71, 10, bar_counter(10), B)
    for k in range(5):
        lv.deco(72 + k * 2, 9, beer_mugs(), B)
    lv.foe(FOE_C, 75, 72, 80, row=10)
    for k in range(4):
        lv.deco(73 + k * 2, 10, stool(), B)
    lv.foe(FOE_B, 84, 82, 88)
    lv.platform(86, 7, fire_escape(4), A)
    lv.solid(91, 10, crate_stack(), A)
    lv.solid(93, 8, crate_stack(), A)
    lv.heart(94, 6)
    lv.deco(96, 2, brick_wall(2, 10, window=False), A)
    # C: the back alley
    drains(99, 2)
    lv.solid(102, 10, dumpster(), A)
    lv.foe(FOE_A, 108, 105, 113)
    lv.platform(110, 8, fire_escape(3), A)
    lv.platform(114, 6, fire_escape(3), A)
    lv.foe(FOE_C, 115, 114, 117, row=6)
    lv.platform(118, 8, fire_escape(3), A)
    drains(115, 4)
    lv.solid(122, 10, trash_can(), A)
    lv.solid(123, 10, trash_can(), A)
    lv.foe(FOE_B, 128, 125, 134)
    lv.solid(135, 10, dumpster(), A)
    lv.platform(139, 7, awning(4), B)
    lv.deco(139, 8, neon_sign(1), B)
    lv.foe(FOE_A, 145, 142, 150)
    drains(151, 2)
    lv.foe(FOE_C, 156, 154, 160)
    lv.solid(160, 10, crate_stack(), A)
    lv.platform(163, 8, awning(4), B)
    lv.foe(FOE_B, 169, 167, 174)
    # D: the punk club stage (boss arena)
    a0 = LEVEL_W_MT - ARENA_MT
    lv.platform(a0 + 3, 9, fire_escape(3), A)
    lv.platform(a0 + 10, 9, fire_escape(3), A)
    lv.deco(a0 + 6, 3, neon_sign(1), B)
    lv.deco(a0 + 8, 3, neon_sign(0), B)
    lv.start()
    return lv


def backdrop():
    W, H = 512, 224
    c = Canvas(W, H)
    pal = pal_grid(PAL_C)
    # night sky bands with stars
    for y in range(H):
        col = 1 if y < 24 else (2 if y < 56 else (3 if y < 88 else 4))
        for x in range(W):
            c.set(x, y, col)
    for k in range(70):
        x = int(noise(k, 1, 81) * W)
        y = int(noise(k, 2, 83) * 90)
        if c.get(x, y) in (1, 2):
            c.set(x, y, 10)
    ellipse(c, 400, 34, 12, 12, 10)                    # moon
    ellipse(c, 405, 31, 10, 10, 13)
    ellipse(c, 403, 32, 9, 9, 10)
    # far skyline (period 256)
    for x0 in range(0, W, 256):
        bx = x0
        k = 0
        while bx < x0 + 256:
            bw = 24 + int(noise(k, x0, 85) * 32)
            bh = 50 + int(noise(k, x0, 87) * 50)
            top = 160 - bh
            fill(c, bx, top, bx + bw, 224, 5 + (k % 3))
            for x in range(bx, bx + bw):
                c.set(x, top, 11)
            for wy in range(top + 6, 152, 10):         # windows
                for wx in range(bx + 4, bx + bw - 4, 7):
                    lit = noise(wx, wy, 89) > 0.55
                    fill(c, wx, wy, wx + 3, wy + 5, 8 if lit else 12)
            bx += bw + 2
            k += 1
    # street lamps and neon signs over the skyline (palette D)
    for x0 in (64, 320):
        fill(c, x0, 96, x0 + 2, 200, 14)
        fill(c, x0 - 6, 94, x0 + 8, 98, 14)
        ellipse(c, x0 - 4, 100, 3, 2, 10)
    for i, x0 in enumerate((152, 232, 408, 480)):
        kind = i % 2
        fill(c, x0, 112, x0 + 32, 128, 10)
        frame_box(c, x0, 112, x0 + 32, 128, 11)
        col, glow = ((2, 3) if kind == 0 else (4, 5))
        # simple neon glyphs: a guitar or a star
        if kind == 0:
            ellipse(c, x0 + 11, 122, 5, 4, col)
            capsule(c, (x0 + 14, 120), (x0 + 28, 114), 0.7, glow)
        else:
            for a in range(5):
                import math
                ang = a * 2 * math.pi / 5 - math.pi / 2
                capsule(c, (x0 + 16, 120), (x0 + 16 + math.cos(ang) * 7, 120 + math.sin(ang) * 7), 0.6, 6)
        set_pal_rect(pal, x0, 112, x0 + 32, 128, PAL_D)
    # storefronts' lower floor, dim brick tone
    for y in range(176, 224):
        for x in range(W):
            c.set(x, y, 15 if y > 178 else 14)
    for x0 in range(0, W, 64):
        fill(c, x0 + 8, 182, x0 + 40, 216, 9)
        fill(c, x0 + 10, 184, x0 + 38, 214, 8 if (x0 // 64) % 3 else 12)
    return c, pal


def main():
    lv = build_level()
    bg2, bg2pal = backdrop()
    export_stage(3, lv, bg2, bg2pal, (P_STREET, P_NEON, P_NIGHT, P_SIGNS), (10, 10, 22))


if __name__ == "__main__":
    main()
