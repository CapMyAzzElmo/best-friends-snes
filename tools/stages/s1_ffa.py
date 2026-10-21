"""Stage 1: the FFA Convention hall, where Jon and Wes met flinging grapes
off spoons. Hay bales, crates, pens, water troughs, a catwalk over the pig
pen, bleachers and the judging tables, then the show ring where the Grand
Champion Bull waits.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pixel import Canvas, capsule, ellipse, shade, outlined
from stagekit import (Level, T_EMPTY, T_SOLID, T_PLATE, PAL_A, PAL_B, PAL_C, PAL_D,
                      FOE_A, FOE_B, FOE_C, ARENA_MT, noise, export_stage)

# --- palettes -------------------------------------------------------------
P_FARM = [(0, 0, 0), (40, 26, 24),
          (252, 232, 140), (232, 192, 88), (196, 148, 60), (140, 100, 44),   # 2-5 hay
          (212, 152, 96), (164, 108, 68), (112, 72, 48),                      # 6-8 wood
          (176, 52, 44),                                                      # 9 twine red
          (172, 132, 96), (132, 96, 70), (94, 66, 50),                        # 10-12 dirt
          (236, 216, 170),                                                    # 13 sawdust
          (184, 192, 208), (110, 118, 140)]                                   # 14-15 steel
P_FFA = [(0, 0, 0), (22, 22, 42),
         (100, 148, 228), (52, 96, 184), (30, 54, 118),                       # 2-4 FFA blue
         (252, 220, 100), (220, 164, 48), (156, 104, 32),                     # 5-7 gold
         (244, 244, 236),                                                     # 8 white
         (180, 108, 212), (126, 66, 166), (78, 34, 106),                      # 9-11 grape
         (100, 180, 76), (54, 114, 50),                                       # 12-13 green
         (204, 208, 220), (122, 126, 148)]                                    # 14-15 bowl steel
P_HALL = [(0, 0, 0), (14, 14, 26),
          (34, 38, 58), (50, 56, 82), (68, 76, 106), (90, 100, 134),          # 2-5 wall
          (92, 64, 50), (128, 92, 66), (168, 124, 86),                        # 6-8 bleachers
          (40, 44, 62), (70, 76, 100),                                        # 9-10 rafters
          (255, 246, 210), (252, 210, 120),                                   # 11-12 lamps
          (164, 186, 220), (116, 136, 178), (206, 224, 250)]                  # 13-15 windows
P_CROWD = [(0, 0, 0), (14, 14, 26),
           (90, 136, 216), (46, 86, 170), (28, 50, 110),                      # 2-4 blue
           (240, 204, 90), (204, 150, 44), (140, 96, 30),                     # 5-7 gold
           (232, 232, 224),                                                   # 8 white
           (30, 32, 50), (46, 50, 72), (64, 68, 94),                          # 9-11 crowd
           (170, 54, 46), (112, 34, 34),                                      # 12-13 red
           (58, 126, 68), (34, 86, 46)]                                       # 14-15 green
PAL_FARM, PAL_FFA, PAL_HALL, PAL_CROWD = PAL_A, PAL_B, PAL_C, PAL_D


# --- metatiles (16x16) ----------------------------------------------------
# Each returns (canvas, palette, [attr top-left, top-right, bottom-left, bottom-right])

def mt_ground_top():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            n = noise(x, y, 1)
            col = 11 if n < 0.55 else (10 if n < 0.8 else 12)
            c.set(x, y, col)
    for x in range(16):        # sawdust crust and grass-like straw tufts
        depth = 3 + (1 if noise(x, 0, 2) > 0.6 else 0)
        for y in range(depth):
            c.set(x, y, 13 if y < depth - 1 else 10)
        if noise(x, 1, 3) > 0.75:
            c.set(x, depth, 13)
    for x in range(16):
        if noise(x, 9, 4) > 0.8:
            c.set(x, 0, 3)
    return c, PAL_FARM, [T_SOLID] * 4


def mt_ground():
    c = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            n = noise(x, y, 5)
            c.set(x, y, 12 if n < 0.45 else (11 if n < 0.9 else 10))
    for (px, py) in ((3, 4), (11, 10), (7, 13)):
        c.set(px, py, 10); c.set(px + 1, py, 11); c.set(px, py + 1, 12)
    return c, PAL_FARM, [T_SOLID] * 4


def hay_bale():
    """32x16 bale -> two metatiles."""
    c = Canvas(32, 16)
    for y in range(1, 15):
        for x in range(1, 31):
            c.set(x, y, 4)
    for x in range(1, 31):
        for y in range(1, 15):
            n = noise(x // 2, y, 7)
            if n > 0.72:
                c.set(x, y, 3)
            elif n < 0.18:
                c.set(x, y, 5)
        # straw strands sticking out of the top
        if noise(x, 0, 8) > 0.6:
            c.set(x, 0, 3)
    for y in range(1, 15):
        c.set(1, y, 5); c.set(30, y, 5)
    for x in range(2, 30):
        c.set(x, 1, 2 if noise(x, 1, 9) > 0.4 else 3)
        c.set(x, 13, 5); c.set(x, 14, 5)
    for bx in (8, 23):           # twine bands
        for y in range(1, 15):
            c.set(bx, y, 9); c.set(bx + 1, y, 1 if y in (1, 14) else 9)
    o = outlined(c, 1)
    # outline sits inside the 32x16 box: redraw border
    for x in range(32):
        o.set(x, 15, 1)
    for y in range(16):
        o.set(0, y, 1); o.set(31, y, 1)
    return o


def crate():
    c = Canvas(32, 32)
    for y in range(32):
        for x in range(32):
            c.set(x, y, 7)
    for y in range(32):          # plank seams
        for x in range(32):
            if y % 8 == 7:
                c.set(x, y, 8)
            elif y % 8 == 0:
                c.set(x, y, 6)
            elif noise(x // 3, y, 11) > 0.85:
                c.set(x, y, 8)
    for i in range(32):          # X brace
        for d in range(-1, 2):
            for (x, y) in ((i + d, i), (31 - i + d, i)):
                if 3 <= x <= 28 and 3 <= y <= 28:
                    c.set(x, y, 6 if d < 0 else (7 if d == 0 else 8))
    for i in range(32):          # frame
        for t in range(3):
            for (x, y) in ((i, t), (i, 31 - t), (t, i), (31 - t, i)):
                c.set(x, y, 6 if t == 1 and (y < 3 or x < 3) else (8 if t == 1 else 7))
    for (x, y) in ((2, 2), (29, 2), (2, 29), (29, 29)):
        c.set(x, y, 14)          # nails
    for i in range(32):
        c.set(i, 0, 1); c.set(i, 31, 1); c.set(0, i, 1); c.set(31, i, 1)
    return c


def table(width_mt):
    """FFA tablecloth table, width_mt metatiles wide, 2 metatiles tall."""
    w = width_mt * 16
    c = Canvas(w, 32)
    for y in range(32):
        for x in range(w):
            c.set(x, y, 3)
    for x in range(w):
        c.set(x, 0, 1); c.set(x, 1, 2); c.set(x, 2, 2); c.set(x, 6, 4)
        c.set(x, 4, 6); c.set(x, 5, 5 if x % 4 else 7)        # gold trim
        for y in range(7, 31):
            if (x % 8) in (0, 1):
                c.set(x, y, 4 if (x % 8) == 0 else 2)          # cloth folds
        c.set(x, 31, 1)
    for y in range(32):
        c.set(0, y, 1); c.set(w - 1, y, 1)
    # FFA emblem: a gold eagle-ish disc in the centre panel
    cx = w // 2
    ellipse(c, cx, 18, 6, 6, 6)
    ellipse(c, cx, 18, 4.5, 4.5, 5)
    for (dx, dy) in ((-2, -1), (-1, -2), (0, -2), (1, -2), (2, -1), (-1, 0), (0, 0), (1, 0), (0, 1)):
        c.set(cx + dx, 18 + dy, 7)
    return c


def grape_bowl():
    c = Canvas(16, 16)
    ellipse(c, 8, 12, 6.5, 3.5, 15)
    for x in range(1, 16):
        c.set(x, 9, 0)
    ellipse(c, 8, 11, 6.5, 2.5, 14)
    for y in range(0, 10):
        for x in range(16):
            pass
    for (gx, gy) in ((5, 8), (8, 8), (11, 8), (6.5, 5.5), (9.5, 5.5), (8, 3)):
        ellipse(c, gx, gy, 1.8, 1.8, 10)
        c.set(int(gx) - 1, int(gy) - 1, 9)
    c.set(8, 1, 12); c.set(9, 0, 13)
    o = outlined(c, 1)
    return o


def fence(top):
    c = Canvas(16, 16)
    for y in range(16):          # post
        c.set(0, y, 15); c.set(1, y, 14); c.set(2, y, 15)
    rails = (2, 9) if top else (3, 10)
    for ry in rails:
        for x in range(16):
            c.set(x, ry, 14); c.set(x, ry + 1, 15)
    if top:
        for x in range(0, 3):
            c.set(x, 0, 14)
    return outlined(c, 1)


def plank():
    c = Canvas(16, 16)
    for x in range(16):
        c.set(x, 0, 1)
        c.set(x, 1, 6); c.set(x, 2, 7); c.set(x, 3, 7); c.set(x, 4, 8); c.set(x, 5, 1)
        if x in (3, 12):
            for y in range(6, 10):
                c.set(x, y, 15)
            c.set(x, 6, 14)
    c.set(7, 2, 8); c.set(8, 3, 8)
    return c


def stage_deck(width_mt):
    w = width_mt * 16
    c = Canvas(w, 16)
    for x in range(w):
        c.set(x, 0, 1); c.set(x, 1, 6)
        for y in range(2, 6):
            c.set(x, y, 7 if (x // 24 + y) % 5 else 8)
        c.set(x, 6, 8); c.set(x, 7, 1)
        for y in range(8, 16):
            c.set(x, y, 8 if x % 16 in (0, 15) else 7)
    return c


def stage_skirt(width_mt, rows):
    w = width_mt * 16
    c = Canvas(w, rows * 16)
    for y in range(rows * 16):
        for x in range(w):
            c.set(x, y, 3 if (x % 12) > 1 else (4 if x % 12 == 0 else 2))
    for x in range(w):
        c.set(x, 0, 6); c.set(x, 1, 5); c.set(x, 2, 7)
    return c


def trophy():
    c = Canvas(32, 32)
    ellipse(c, 16, 10, 9, 8, 6)
    for x in range(5, 28):
        for y in range(0, 4):
            c.set(x, y, 0)
    capsule(c, (7, 6), (3, 10), 1.2, 6)
    capsule(c, (3, 10), (8, 14), 1.2, 6)
    capsule(c, (25, 6), (29, 10), 1.2, 6)
    capsule(c, (29, 10), (24, 14), 1.2, 6)
    capsule(c, (16, 17), (16, 23), 2, 6)
    for y in range(24, 31):
        for x in range(9, 24):
            c.set(x, y, 4 if y > 26 else 7)
    shade(c, 6, 5, 7)
    for (x, y) in ((11, 6), (11, 7), (12, 5), (12, 8)):
        c.set(x, y, 8)
    for x in range(12, 21):
        c.set(x, 28, 5)
    return outlined(c, 1)


# --- level assembly -------------------------------------------------------
LEVEL_W_MT = 176


def trough(part):
    """Water trough sunk into the floor: part 0 left end, 1 middle, 2 right end."""
    c = Canvas(16, 32)
    for y in range(32):
        for x in range(16):
            c.set(x, y, 12 if y > 20 else 0)
    for y in range(4, 22):
        for x in range(16):
            if y < 7:
                c.set(x, y, 13 if (x + y) % 5 == 0 else 14)   # water surface glints
            else:
                c.set(x, y, 15 if (y // 3 + x // 4) % 3 else 14)
    for x in range(16):
        c.set(x, 3, 1); c.set(x, 21, 1)
    if part == 0:
        for y in range(0, 22):
            c.set(0, y, 1); c.set(1, y, 14); c.set(2, y, 15)
    if part == 2:
        for y in range(0, 22):
            c.set(15, y, 1); c.set(14, y, 15); c.set(13, y, 15)
    return c


def build_level():
    lv = Level(LEVEL_W_MT)
    lv.floor(mt_ground_top(), mt_ground())

    bale, box = hay_bale(), crate()
    def bales(mx, my, n=1):
        for i in range(n):
            lv.put_big(mx + 2 * i, my, bale, PAL_FARM, "all")
    def crates(mx, my):
        lv.put_big(mx, my, box, PAL_FARM, "all")
    def tables(mx, my, wmt, bowl=True):
        lv.put_big(mx, my, table(wmt), PAL_FFA, plate_top=True)
        if bowl:
            lv.put(mx + wmt // 2, my - 1, (grape_bowl(), PAL_FFA, [T_EMPTY] * 4))
    def fences(mx, n):
        for i in range(n):
            lv.put(mx + i, 10, (fence(True), PAL_FARM, [T_EMPTY] * 4))
            lv.put(mx + i, 11, (fence(False), PAL_FARM, [T_EMPTY] * 4))
    pl = plank()
    def planks(mx, my, n):
        for i in range(n):
            lv.put(mx + i, my, (pl, PAL_FARM, [T_PLATE, T_PLATE, T_EMPTY, T_EMPTY]))
    def troughs(mx, n):
        lv.hazard(mx, n, trough, PAL_FARM)
    enemy, heart = lv.foe, lv.heart
    OBJ_GOAT, OBJ_PIG, OBJ_CHICKEN = FOE_A, FOE_B, FOE_C

    # A: the welcome pens
    fences(2, 5)
    tables(9, 10, 3)
    bales(14, 11, 2)
    bales(15, 10, 1)
    enemy(OBJ_GOAT, 21, 19, 27)
    # B: the poultry barn, climb the crates and planks
    crates(27, 10)
    planks(30, 8, 3)
    planks(34, 6, 3)
    heart(35, 5)
    enemy(OBJ_CHICKEN, 31, 30, 33, row=8)
    enemy(OBJ_CHICKEN, 37, 33, 41)
    crates(40, 10)
    crates(42, 10)
    crates(42, 8)
    enemy(OBJ_CHICKEN, 45, 44, 47)
    # C: water troughs
    troughs(48, 3)
    bales(51, 11, 1)
    troughs(53, 3)
    bales(56, 11, 1)
    troughs(58, 4)
    enemy(OBJ_GOAT, 66, 63, 70)
    # D: the catwalk over the pig pen
    bales(70, 11, 2)
    bales(71, 10, 1)
    planks(72, 8, 6)
    planks(80, 8, 5)
    planks(87, 8, 6)
    fences(76, 5)
    enemy(OBJ_PIG, 82, 74, 94)
    enemy(OBJ_CHICKEN, 89, 87, 92, row=8)
    # E: the bleacher climb
    planks(97, 10, 2)
    planks(100, 8, 2)
    planks(103, 6, 3)
    heart(104, 5)
    planks(107, 8, 2)
    planks(110, 10, 2)
    enemy(OBJ_GOAT, 103, 98, 113)
    enemy(OBJ_CHICKEN, 116, 113, 120)
    # F: the judging tables
    tables(121, 10, 4)
    enemy(OBJ_CHICKEN, 127, 125, 131)
    bales(134, 11, 2)
    enemy(OBJ_PIG, 131, 126, 140)
    # G: the prize stage, now a gauntlet of crates over the sawdust pit
    bales(141, 11, 1)
    lv.put_big(144, 9, stage_deck(6), PAL_FARM, plate_top=True)
    lv.put_big(144, 10, stage_skirt(6, 2), PAL_FFA)
    troughs(151, 2)
    crates(153, 10)
    troughs(155, 2)
    tables(157, 10, 2, bowl=False)
    enemy(OBJ_GOAT, 145, 144, 149, row=9)
    heart(158, 8)
    # H: the show ring (boss arena)
    a0 = LEVEL_W_MT - ARENA_MT
    fences(a0, 2)
    fences(LEVEL_W_MT - 2, 2)
    planks(a0 + 3, 9, 3)
    planks(a0 + 10, 9, 3)
    lv.start()
    return lv


# --- BG2: the hall backdrop ---------------------------------------------------
def hall_backdrop():
    W, H = 512, 224
    c = Canvas(W, H)
    pal = [[PAL_HALL] * (W // 8) for _ in range(H // 8)]
    # ceiling and rafters (rows 0-47)
    for y in range(0, 48):
        for x in range(W):
            c.set(x, y, 2 if y < 40 else 3)
    for x0 in range(0, W, 64):                        # trusses
        for x in range(64):
            for t in (8, 9, 38, 39):
                c.set(x0 + x, t, 10 if t in (8, 38) else 9)
        for i in range(30):
            for (x, y) in ((x0 + i, 9 + i), (x0 + 63 - i, 9 + i)):
                if y < 38:
                    c.set(x, y, 9); c.set(x + 1, y, 10)
    for x0 in range(32, W, 128):                      # hanging lamps
        for y in range(10, 22):
            c.set(x0, y, 9)
        ellipse(c, x0, 24, 5, 3, 10)
        for x in range(x0 - 5, x0 + 6):
            c.set(x, 22, 9)
        ellipse(c, x0, 26, 3, 1.5, 11)
        for y in range(28, 46):                       # soft light cone
            half = 3 + (y - 28) // 2
            for x in range(x0 - half, x0 + half + 1):
                if (x + y) % 2 == 0 and c.get(x, y) in (2, 3):
                    c.set(x, y, 4 if y < 40 else 5)
    # upper wall with tall windows (rows 48-111)
    for y in range(48, 112):
        for x in range(W):
            course = (y - 48) // 8
            seam = (x + (course % 2) * 16) % 32 == 0
            c.set(x, y, 2 if (y % 8 == 0 or seam) else (4 if y % 8 == 1 and noise(x // 8, course, 21) > 0.5 else 3))
    for x0 in range(64, W, 128):
        for y in range(54, 104):
            for x in range(x0 - 14, x0 + 14):
                inner = (x - (x0 - 14)) % 14 not in (0, 13) and (y - 54) % 25 not in (0, 24)
                if inner:
                    g = (y - 54) / 50
                    c.set(x, y, 15 if g < 0.3 else (13 if g < 0.7 else 14))
                else:
                    c.set(x, y, 4)
        for y in range(54, 104):
            c.set(x0 - 15, y, 5); c.set(x0 + 14, y, 2)
        for x in range(x0 - 15, x0 + 15):
            c.set(x, 104, 5); c.set(x, 105, 2)
    # banners between windows (palette 6)
    banner_colors = [(3, 2, 4, 6), (12, 12, 13, 6), (14, 14, 15, 5), (3, 2, 4, 5)]
    for i, x0 in enumerate(range(0, W, 128)):
        mid, light, dark, trim = banner_colors[i % 4]
        bx = x0 + 4
        for y in range(48, 100):
            for x in range(bx, bx + 24):
                c.set(x, y, mid)
            c.set(bx, y, light); c.set(bx + 23, y, dark)
        for x in range(bx, bx + 24):
            c.set(x, 48, 7); c.set(x, 49, trim)
        for x in range(bx, bx + 24):                   # swallowtail bottom
            d = abs(x - (bx + 11.5))
            for y in range(100, int(100 + d / 2) + 1):
                c.set(x, y, mid)
        ellipse(c, bx + 12, 66, 7, 7, trim)            # emblem
        ellipse(c, bx + 12, 66, 5, 5, mid)
        ellipse(c, bx + 12, 66, 2.5, 2.5, 8)
        for y in range(80, 90, 3):                     # stripes
            for x in range(bx + 4, bx + 20):
                c.set(x, y, trim)
        for ty in range(48 // 8, 112 // 8):
            for tx in range(bx // 8, (bx + 24) // 8):
                pal[ty][tx] = PAL_CROWD
    # bleachers with the crowd (rows 112-191), kept dim so the playfield pops
    for y in range(112, 192):
        yy = (y - 112) % 16
        for x in range(W):
            col = 11 if yy < 1 else (10 if yy < 4 else (9 if yy < 13 else 1))
            if yy >= 4 and yy < 13 and x % 32 == 0:
                col = 1                                # seat supports
            c.set(x, y, col)
    for ty in range(112 // 8, 192 // 8):
        for tx in range(W // 8):
            pal[ty][tx] = PAL_CROWD
    crowd = Canvas(512, 80)
    for row in range(5):
        base = row * 16 + 1
        for x0 in range(0, 512, 12):
            if noise(x0, row, 37) < 0.18:
                continue                               # empty seats
            jitter = int(noise(x0 // 12, row, 31) * 2)
            hx = x0 + 6 + (row % 2) * 6
            shirt = [4, 13, 15, 3, 9][int(noise(x0, row, 33) * 5)]
            capsule(crowd, (hx - 3, base + 10), (hx + 3, base + 10), 2.6, shirt)
            ellipse(crowd, hx, base + 4 - jitter, 2.3, 2.5, 7)
            if noise(x0, row, 35) > 0.55:              # caps
                for x in range(hx - 2, hx + 3):
                    crowd.set(x, base + 2 - jitter, [4, 13, 6][row % 3])
    for y in range(80):
        for x in range(512):
            v = crowd.px[y][x]
            if v:
                c.set(x, 112 + y, v)
    # darken the crowd's lower rows for depth (crowd palette indices 9-11)
    # lower wall boards behind the arena floor (rows 192-223)
    for y in range(192, 224):
        for x in range(W):
            c.set(x, y, 1 if y < 194 else (3 if (x // 32 + y // 8) % 2 else 2))
    return c, pal


def main():
    lv = build_level()
    bg2, bg2pal = hall_backdrop()
    export_stage(1, lv, bg2, bg2pal, (P_FARM, P_FFA, P_HALL, P_CROWD), (14, 14, 26))


if __name__ == "__main__":
    main()
