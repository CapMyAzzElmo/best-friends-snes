"""Builds Stage 1, the FFA Convention hall.

BG1 (playfield) is assembled from 16x16 metatiles placed on a grid, so the
level reuses a small set of 8x8 tiles. BG2 is a 512px wide repeating hall
backdrop (rafters, windows, banners, bleachers) that scrolls at half speed.

Outputs (in build/):
  stage1_bg1.pic/.pal   BG1 tiles (4bpp) and BG palettes 1-2
  stage1.m16/.t16/.b16  map engine data (map, tile palette/priority, collision)
  stage1.o16            object list (player start, goats, goal)
  stage1_bg2.pic/.pal/.map  BG2 tiles, palettes 5-6 and 64x32 tilemap
and art/bg/stage1_preview.png for review.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image
from pixel import Canvas, capsule, ellipse, shade, outlined
from snesgfx import tile_4bpp, palette_bytes, words

ROOT = os.path.join(os.path.dirname(__file__), "..")
BUILD = os.path.join(ROOT, "build")
ART = os.path.join(ROOT, "art", "bg")

T_EMPTY, T_SOLID, T_PLATE = 0x0000, 0xFF00, 0x0008

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
PAL_FARM, PAL_FFA, PAL_HALL, PAL_CROWD = 1, 2, 5, 6


def noise(x, y, seed=0):
    """Deterministic hash noise in [0, 1)."""
    n = (x * 374761393 + y * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


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
LEVEL_W_MT = 150
LEVEL_H_MT = 14


class Level:
    def __init__(self):
        self.cells = {}           # (mx, my) -> (canvas16, palette, attrs)
        self.objects = []         # (x, y, type, minx, maxx)

    def put(self, mx, my, mt):
        self.cells[(mx, my)] = mt

    def put_big(self, mx, my, canvas, pal, solid_rows=None, plate_top=False):
        """Split a larger canvas into metatiles. solid_rows: set of 8px rows that are solid."""
        for ty in range(canvas.h // 16):
            for tx in range(canvas.w // 16):
                sub = Canvas(16, 16)
                for y in range(16):
                    for x in range(16):
                        sub.px[y][x] = canvas.px[ty * 16 + y][tx * 16 + x]
                attrs = []
                for r in range(2):
                    for _ in range(2):
                        row8 = ty * 2 + r
                        if solid_rows == "all":
                            attrs.append(T_SOLID)
                        elif plate_top and row8 == 0:
                            attrs.append(T_PLATE)
                        else:
                            attrs.append(T_EMPTY)
                self.put(mx + tx, my + ty, (sub, pal, attrs))


def build_level():
    lv = Level()
    gt, gf = mt_ground_top(), mt_ground()
    for mx in range(LEVEL_W_MT):
        lv.put(mx, 12, gt)
        lv.put(mx, 13, gf)

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
    def goat(mx, lo, hi):
        lv.objects.append((mx * 16, 11 * 16 - 16, 1, lo * 16, hi * 16))

    # opening: pens and a welcome table
    fences(2, 6)
    tables(11, 10, 3)
    bales(17, 11, 2)
    bales(18, 10, 1)
    goat(26, 22, 32)
    crates(33, 10)
    crates(35, 10)
    crates(35, 8)
    planks(38, 7, 3)
    bales(43, 11, 3)
    bales(45, 10, 2)
    bales(46, 9, 1)
    goat(52, 50, 60)
    fences(54, 5)
    tables(61, 10, 4)
    planks(66, 8, 2)
    planks(70, 6, 3)
    planks(75, 8, 2)
    goat(72, 68, 80)
    bales(80, 11, 2)
    bales(84, 11, 2)
    bales(82, 10, 2)
    bales(83, 9, 1)
    goat(90, 87, 94)
    crates(95, 10)
    crates(97, 10)
    crates(97, 8)
    crates(99, 10)
    crates(101, 10)
    planks(103, 8, 2)
    tables(106, 10, 3)
    goat(112, 109, 120)
    fences(114, 4)
    bales(120, 11, 2)
    goat(126, 124, 132)
    # finale: the convention stage with the champion trophy
    lv.put_big(134, 9, stage_deck(16), PAL_FARM, plate_top=True)
    lv.put_big(134, 10, stage_skirt(16, 2), PAL_FFA)
    lv.put_big(142, 7, trophy(), PAL_FFA)
    bales(131, 11, 1)
    lv.objects.insert(0, (32, 11 * 16 - 48, 0, 0, 0))     # player start
    lv.objects.append((142 * 16, 7 * 16, 2, 0, 0))         # goal
    return lv


def export_bg1(lv):
    tiles = [tuple(tuple(0 for _ in range(8)) for _ in range(8))]  # tile 0 = blank
    tile_pal = [PAL_FARM]
    tile_attr = [T_EMPTY]
    index = {(tiles[0], PAL_FARM, T_EMPTY): 0}
    W, H = LEVEL_W_MT * 2, LEVEL_H_MT * 2
    grid = [[0] * W for _ in range(H)]
    for (mx, my), (cv, pal, attrs) in lv.cells.items():
        for q in range(4):
            qx, qy = q % 2, q // 2
            px = tuple(tuple(cv.px[qy * 8 + y][qx * 8 + x] for x in range(8)) for y in range(8))
            attr = attrs[q]
            if not any(any(r) for r in px) and attr == T_EMPTY:
                key = (tiles[0], PAL_FARM, T_EMPTY)
            else:
                key = (px, pal, attr)
            if key not in index:
                index[key] = len(tiles)
                tiles.append(px)
                tile_pal.append(pal)
                tile_attr.append(attr)
            grid[my * 2 + qy][mx * 2 + qx] = index[key]
    # tiles are deduplicated with their attribute, so the same picture may
    # appear twice (solid vs. empty); VRAM data is shared by remapping.
    vram = {}
    vram_tiles = []
    t16 = []
    for i, px in enumerate(tiles):
        if px not in vram:
            vram[px] = len(vram_tiles)
            vram_tiles.append(px)
        t16.append(vram[px] | (tile_pal[i] << 10))
    print(f"BG1: {len(tiles)} map tiles, {len(vram_tiles)} unique VRAM tiles")
    assert len(vram_tiles) <= 512, "BG1 tile budget exceeded"
    assert len(tiles) <= 1024

    with open(os.path.join(BUILD, "stage1_bg1.pic"), "wb") as f:
        for px in vram_tiles:
            f.write(tile_4bpp(px))
    with open(os.path.join(BUILD, "stage1.m16"), "wb") as f:
        f.write(words([W * 8, H * 8, W * H * 2]))
        f.write(words([grid[y][x] for y in range(H) for x in range(W)]))
    with open(os.path.join(BUILD, "stage1.t16"), "wb") as f:
        f.write(words(t16 + [0] * (2048 - len(t16))))
    with open(os.path.join(BUILD, "stage1.b16"), "wb") as f:
        f.write(words(tile_attr + [0] * (1024 - len(tile_attr))))
    goats = [o for o in lv.objects if o[2] == 1]
    start = [o for o in lv.objects if o[2] == 0][0]
    goal = [o for o in lv.objects if o[2] == 2][0]
    with open(os.path.join(BUILD, "stage1_hero.o16"), "wb") as f:
        f.write(words([start[0], start[1], 0, 0, 0, 0xFFFF]))
    with open(os.path.join(BUILD, "stage1_objects.h"), "w") as f:
        f.write("// generated by tools/ffa_stage.py\n")
        f.write(f"#define STAGE1_START_X {start[0]}\n#define STAGE1_START_Y {start[1]}\n")
        f.write(f"#define STAGE1_GOAL_X {goal[0]}\n#define STAGE1_NGOATS {len(goats)}\n")
        f.write("const u16 stage1_goats[] = {\n")
        for g in goats:
            f.write(f"    {g[0]}, {g[3]}, {g[4]},\n")
        f.write("};\n")
    return grid, tiles, tile_pal


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


def export_bg2():
    c, pal = hall_backdrop()
    tiles = {}
    tile_list = []
    tmap = [[0] * 64 for _ in range(32)]
    for ty in range(28):
        for tx in range(64):
            px = tuple(tuple(c.px[ty * 8 + y][tx * 8 + x] for x in range(8)) for y in range(8))
            flip = None
            key = px
            if key not in tiles:
                tiles[key] = len(tile_list)
                tile_list.append(px)
            tmap[ty][tx] = tiles[key] | (pal[ty][tx] << 10)
    print(f"BG2: {len(tile_list)} unique tiles")
    assert len(tile_list) <= 512, "BG2 tile budget exceeded"
    with open(os.path.join(BUILD, "stage1_bg2.pic"), "wb") as f:
        for px in tile_list:
            f.write(tile_4bpp(px))
    # SC_64x32 layout: left 32x32 screen then right 32x32 screen
    data = []
    for screen in range(2):
        for y in range(32):
            for x in range(32):
                data.append(tmap[y][screen * 32 + x])
    with open(os.path.join(BUILD, "stage1_bg2.map"), "wb") as f:
        f.write(words(data))
    return c, pal


def export_palettes():
    pals = [[(0, 0, 0)] * 16 for _ in range(8)]
    pals[0][0] = (14, 14, 26)              # backdrop colour
    pals[PAL_FARM] = P_FARM
    pals[PAL_FFA] = P_FFA
    pals[PAL_HALL] = P_HALL
    pals[PAL_CROWD] = P_CROWD
    with open(os.path.join(BUILD, "stage1_bg.pal"), "wb") as f:
        for p in pals:
            f.write(palette_bytes(p))
    return pals


def preview(lv, grid, tiles, tile_pal, bg2, bg2pal, pals, x0=0, width=1024):
    snap = lambda rgb: tuple((v >> 3) << 3 for v in rgb)
    img = Image.new("RGB", (width, 224))
    pix = img.load()
    for y in range(224):
        for x in range(width):
            bx = (x0 // 2 + x) % 512
            v = bg2.px[y][bx]
            p = bg2pal[y // 8][bx // 8]
            pix[x, y] = snap(pals[p][v])
            lx = x0 + x
            t = grid[y // 8][lx // 8]
            tv = tiles[t][y % 8][lx % 8]
            if tv:
                pix[x, y] = snap(pals[tile_pal[t]][tv])
    return img


def main():
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(ART, exist_ok=True)
    lv = build_level()
    grid, tiles, tile_pal = export_bg1(lv)
    bg2, bg2pal = export_bg2()
    pals = export_palettes()
    preview(lv, grid, tiles, tile_pal, bg2, bg2pal, pals, 0, 2400).save(os.path.join(ART, "stage1_preview.png"))


if __name__ == "__main__":
    main()
