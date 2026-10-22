"""Shared stage building kit.

A stage is a BG1 playfield assembled from 16x16 metatiles on a grid (so the
level reuses a small set of 8x8 tiles), plus a 512px wide repeating BG2
backdrop that scrolls at half speed.

Every stage module (tools/stages/sN_*.py) builds a Level and a backdrop and
calls export_stage(), which writes for stage N (in build/):
  stN_bg1.pic           BG1 tiles (4bpp)
  stN.m16/.t16/.b16     map engine data (map, tile palette/priority, collision)
  stN_hero.o16          hero start (object engine table, lives in ROM)
  stN_bg2.pic/.map      BG2 tiles and 64x32 tilemap
  stN_bg.pal            BG palettes 0-7
  stN_info.h            foes, hearts, boss arena position
and art/bg/stN_preview.png for review.

BG palette slots used by stages: 1 and 2 for the playfield, 5 and 6 for the
backdrop (0 is UI text, 3 the title logo).
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
PAL_A, PAL_B, PAL_C, PAL_D = 1, 2, 5, 6        # playfield x2, backdrop x2

# object kinds (match src/game.h)
OBJ_START, FOE_A, FOE_B, FOE_C, OBJ_HEART = 0, 1, 2, 3, 5
GAD_SPOON, GAD_RAFT = 1, 2

LEVEL_H_MT = 14
ARENA_MT = 16                                    # boss arena: the last screen


def noise(x, y, seed=0):
    """Deterministic hash noise in [0, 1)."""
    n = (x * 374761393 + y * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


def fill(c, x0, y0, x1, y1, col):
    for y in range(max(0, y0), min(c.h, y1)):
        for x in range(max(0, x0), min(c.w, x1)):
            c.px[y][x] = col


def frame_box(c, x0, y0, x1, y1, col):
    for x in range(x0, x1):
        c.set(x, y0, col); c.set(x, y1 - 1, col)
    for y in range(y0, y1):
        c.set(x0, y, col); c.set(x1 - 1, y, col)


class Level:
    def __init__(self, width_mt):
        self.w = width_mt
        self.cells = {}           # (mx, my) -> (canvas16, palette, attrs)
        self.objects = []         # (x, y, kind, minx, maxx)
        self.gadgets = []         # (kind, x, feet y, max x)

    def put(self, mx, my, mt, merge=True):
        """Place a metatile. Over an existing cell with the same palette the
        new pixels are drawn on top, and a non-empty attribute wins."""
        old = self.cells.get((mx, my))
        if merge and old is not None and old[1] == mt[1]:
            cv = old[0].copy()
            cv.blit(mt[0])
            attrs = [n if n != T_EMPTY else o for n, o in zip(mt[2], old[2])]
            mt = (cv, mt[1], attrs)
        self.cells[(mx, my)] = mt

    def put_big(self, mx, my, canvas, pal, solid_rows=None, plate_top=False, attr_rows=None, merge=True):
        """Split a larger canvas into metatiles.
        solid_rows="all": every tile solid. plate_top: top 8px row is a one-way
        platform. attr_rows: explicit attribute per 8px row."""
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
                        if attr_rows is not None:
                            attrs.append(attr_rows[row8])
                        elif solid_rows == "all":
                            attrs.append(T_SOLID)
                        elif plate_top and row8 == 0:
                            attrs.append(T_PLATE)
                        else:
                            attrs.append(T_EMPTY)
                self.put(mx + tx, my + ty, (sub, pal, attrs), merge)

    def deco(self, mx, my, canvas, pal):
        """Background-only decoration (no collision)."""
        self.put_big(mx, my, canvas, pal)

    def solid(self, mx, my, canvas, pal):
        self.put_big(mx, my, canvas, pal, "all")

    def platform(self, mx, my, canvas, pal):
        self.put_big(mx, my, canvas, pal, plate_top=True)

    def floor(self, mt_top, mt_fill, x0=0, x1=None):
        for mx in range(x0, self.w if x1 is None else x1):
            self.put(mx, 12, mt_top)
            self.put(mx, 13, mt_fill)

    def hazard(self, mx, n, part_fn, pal):
        """A hazard sunk into the floor (water, mud, a pit): only the bottom
        8px row is solid, and landing there hurts and bounces the hero out.
        part_fn(part) gives a 16x32 canvas, part 0 left end, 1 middle, 2 right."""
        for i in range(n):
            part = 0 if i == 0 else (2 if i == n - 1 else 1)
            self.put_big(mx + i, 12, part_fn(part), pal, attr_rows=[T_EMPTY, T_EMPTY, T_EMPTY, T_SOLID],
                         merge=False)

    def foe(self, kind, mx, lo, hi, row=12):
        self.objects.append((mx * 16, row * 16, kind, lo * 16, hi * 16))

    def spoon(self, mx, row=12):
        """A giant spoon catapult on the floor: step on it to be flung up high."""
        self.gadgets.append((GAD_SPOON, mx * 16, row * 16, 0))

    def raft(self, mx0, mx1, top=190):
        """A pool raft drifting back and forth between mx0 and mx1 (metatiles)."""
        self.gadgets.append((GAD_RAFT, mx0 * 16, top, mx1 * 16 - 32))

    def heart(self, mx, row):
        self.objects.append((mx * 16, row * 16, OBJ_HEART, 0, 0))

    def start(self, x=32):
        self.objects.insert(0, (x, 11 * 16 - 32, OBJ_START, 0, 0))


def export_bg1(n, lv):
    tiles = [tuple(tuple(0 for _ in range(8)) for _ in range(8))]  # tile 0 = blank
    tile_pal = [PAL_A]
    tile_attr = [T_EMPTY]
    index = {(tiles[0], PAL_A, T_EMPTY): 0}
    W, H = lv.w * 2, LEVEL_H_MT * 2
    grid = [[0] * W for _ in range(H)]
    for (mx, my), (cv, pal, attrs) in lv.cells.items():
        if mx >= lv.w or my >= LEVEL_H_MT:
            continue
        for q in range(4):
            qx, qy = q % 2, q // 2
            px = tuple(tuple(cv.px[qy * 8 + y][qx * 8 + x] for x in range(8)) for y in range(8))
            attr = attrs[q]
            if not any(any(r) for r in px) and attr == T_EMPTY:
                key = (tiles[0], PAL_A, T_EMPTY)
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
    print(f"st{n} BG1: {len(tiles)} map tiles, {len(vram_tiles)} unique VRAM tiles, {lv.w * 16}px wide")
    assert len(vram_tiles) <= 512, "BG1 tile budget exceeded"
    assert len(tiles) <= 1024, "BG1 map tile budget exceeded"

    with open(os.path.join(BUILD, f"st{n}_bg1.pic"), "wb") as f:
        for px in vram_tiles:
            f.write(tile_4bpp(px))
    with open(os.path.join(BUILD, f"st{n}.m16"), "wb") as f:
        f.write(words([W * 8, H * 8, W * H * 2]))
        f.write(words([grid[y][x] for y in range(H) for x in range(W)]))
    with open(os.path.join(BUILD, f"st{n}.t16"), "wb") as f:
        f.write(words(t16 + [0] * (2048 - len(t16))))
    with open(os.path.join(BUILD, f"st{n}.b16"), "wb") as f:
        f.write(words(tile_attr + [0] * (1024 - len(tile_attr))))
    coll = [[tile_attr[grid[y][x]] for x in range(W)] for y in range(H)]
    return grid, tiles, tile_pal, coll


# breakable prop contents (match ITEM_* in src/game.h)
ITEM_STAR, ITEM_HEART, ITEM_1UP, ITEM_SPREAD, ITEM_RAPID, ITEM_RANG, ITEM_BOMB = range(7)
WEAPONS = [ITEM_SPREAD, ITEM_RAPID, ITEM_RANG, ITEM_BOMB]


def surfaces(coll, tx):
    """Rows (8px) a hero can stand on in column tx, top first, skipping hazard floors."""
    H = len(coll)
    out = []
    for y in range(1, H):
        if coll[y][tx] in (T_SOLID, T_PLATE) and coll[y - 1][tx] not in (T_SOLID, T_PLATE):
            if y < H - 1 and all(coll[y - k][tx] != T_SOLID for k in range(1, 5) if y - k >= 0):
                out.append(y)
    return out


def place_props(n, lv, coll):
    """Breakable props every so often along the stage (on the highest safe
    surface, so some sit up on platforms), and two checkpoint flags."""
    arena = lv.w - ARENA_MT
    props = []
    pattern = ["W", ITEM_STAR, ITEM_HEART, ITEM_STAR, "W", ITEM_STAR, ITEM_1UP, ITEM_STAR, "W", ITEM_HEART,
               ITEM_STAR, "W", ITEM_STAR, ITEM_HEART]
    weapon = n - 1
    mx = 9
    k = 0
    while mx < arena - 4:
        found = None
        for dx in range(0, 4):
            tx = (mx + dx) * 2
            # both 8px columns under the 16px prop must agree
            a, b = surfaces(coll, tx), surfaces(coll, tx + 1)
            common = [y for y in a if y in b and 8 <= y <= 24]
            if common:
                found = ((mx + dx) * 16, common[0] * 8)
                break
        if found:
            item = pattern[k % len(pattern)]
            if item == "W":
                item = WEAPONS[weapon % 4]
                weapon += 1
            props.append((found[0], found[1], item))
            k += 1
        mx += 11 + (k * 7) % 5
    cps = []
    for frac in (0.36, 0.68):
        mx = int(arena * frac)
        for dx in range(0, 12):
            tx = (mx + dx) * 2
            a, b = surfaces(coll, tx), surfaces(coll, tx + 1)
            ground = [y for y in a if y in b and y >= 20]
            if ground:
                cps.append(((mx + dx) * 16, ground[-1] * 8))
                break
    return props, cps


def export_objects(n, lv, coll):
    start = [o for o in lv.objects if o[2] == OBJ_START][0]
    foes = sorted([o for o in lv.objects if o[2] in (FOE_A, FOE_B, FOE_C)], key=lambda o: o[0])
    hearts = [o for o in lv.objects if o[2] == OBJ_HEART]
    arena = (lv.w - ARENA_MT) * 16
    assert len(foes) <= 24 and len(hearts) <= 6
    with open(os.path.join(BUILD, f"st{n}_hero.o16"), "wb") as f:
        f.write(words([start[0], start[1], 0, 0, 0, 0xFFFF]))
    with open(os.path.join(BUILD, f"st{n}_info.h"), "w") as f:
        f.write(f"// generated by tools/stagekit.py\n")
        f.write(f"#define ST{n}_ARENA_X {arena}\n#define ST{n}_NFOES {len(foes)}\n")
        f.write(f"#define ST{n}_NHEARTS {len(hearts)}\n")
        f.write("// kind, x, feet y, min x, max x\n")
        f.write(f"const u16 st{n}_foetab[] = {{\n")
        for o in foes:
            f.write(f"    {o[2]}, {o[0]}, {o[1]}, {o[3]}, {o[4]},\n")
        f.write("    0};\n")
        f.write(f"const u16 st{n}_hearttab[] = {{\n")
        for o in hearts:
            f.write(f"    {o[0]}, {o[1]},\n")
        f.write("    0};\n")
        props, cps = place_props(n, lv, coll)
        assert len(props) <= 16 and len(cps) == 2, (len(props), cps)
        f.write(f"#define ST{n}_NPROPS {len(props)}\n")
        f.write("// breakable props: x, feet y, item\n")
        f.write(f"const u16 st{n}_proptab[] = {{\n")
        for p in props:
            f.write(f"    {p[0]}, {p[1]}, {p[2]},\n")
        f.write("    0};\n")
        assert len(lv.gadgets) <= 6
        f.write(f"#define ST{n}_NGADS {len(lv.gadgets)}\n")
        f.write("// spoon catapults and rafts: kind, x, feet y, max x\n")
        f.write(f"const u16 st{n}_gadtab[] = {{\n")
        for g in lv.gadgets:
            f.write(f"    {g[0]}, {g[1]}, {g[2]}, {g[3]},\n")
        f.write("    0};\n")
        f.write("// checkpoint flags: x, feet y\n")
        f.write(f"const u16 st{n}_cptab[] = {{\n")
        for p in cps:
            f.write(f"    {p[0]}, {p[1]},\n")
        f.write("    0};\n")
    return props, cps


def export_bg2(n, c, pal):
    """c: 512x224 canvas, pal: per 8x8 cell palette grid (28 x 64)."""
    tiles = {}
    tile_list = []
    tmap = [[0] * 64 for _ in range(32)]
    for ty in range(28):
        for tx in range(64):
            px = tuple(tuple(c.px[ty * 8 + y][tx * 8 + x] for x in range(8)) for y in range(8))
            if px not in tiles:
                tiles[px] = len(tile_list)
                tile_list.append(px)
            tmap[ty][tx] = tiles[px] | (pal[ty][tx] << 10)
    print(f"st{n} BG2: {len(tile_list)} unique tiles")
    assert len(tile_list) <= 512, "BG2 tile budget exceeded"
    with open(os.path.join(BUILD, f"st{n}_bg2.pic"), "wb") as f:
        for px in tile_list:
            f.write(tile_4bpp(px))
    # SC_64x32 layout: left 32x32 screen then right 32x32 screen
    data = []
    for screen in range(2):
        for y in range(32):
            for x in range(32):
                data.append(tmap[y][screen * 32 + x])
    with open(os.path.join(BUILD, f"st{n}_bg2.map"), "wb") as f:
        f.write(words(data))


def export_palettes(n, pa, pb, pc, pd, backdrop):
    pals = [[(0, 0, 0)] * 16 for _ in range(8)]
    pals[0][0] = backdrop
    pals[PAL_A], pals[PAL_B], pals[PAL_C], pals[PAL_D] = pa, pb, pc, pd
    with open(os.path.join(BUILD, f"st{n}_bg.pal"), "wb") as f:
        for p in pals:
            f.write(palette_bytes(p))
    return pals


def preview(grid, tiles, tile_pal, bg2, bg2pal, pals, x0=0, width=1024):
    snap = lambda rgb: tuple((v >> 3) << 3 for v in rgb)
    img = Image.new("RGB", (width, 224))
    pix = img.load()
    for y in range(224):
        for x in range(width):
            bx = (x0 // 2 + x) % 512
            v = bg2.px[y][bx]
            p = bg2pal[y // 8][bx // 8]
            pix[x, y] = snap(pals[p][v] if v else pals[0][0])
            lx = x0 + x
            if lx // 8 >= len(grid[0]):
                continue
            t = grid[y // 8][lx // 8]
            tv = tiles[t][y % 8][lx % 8]
            if tv:
                pix[x, y] = snap(pals[tile_pal[t]][tv])
    return img


def export_stage(n, lv, backdrop_canvas, backdrop_pal, palettes, backdrop_color):
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(ART, exist_ok=True)
    grid, tiles, tile_pal, coll = export_bg1(n, lv)
    props, cps = export_objects(n, lv, coll)
    export_bg2(n, backdrop_canvas, backdrop_pal)
    pals = export_palettes(n, *palettes, backdrop_color)
    img = preview(grid, tiles, tile_pal, backdrop_canvas, backdrop_pal, pals, 0, lv.w * 16)
    # mark the props (yellow) and checkpoints (red) on the preview
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for x, y, _ in props:
        d.rectangle([x, y - 16, x + 15, y - 1], outline=(255, 230, 0))
    for x, y in cps:
        d.rectangle([x + 3, y - 16, x + 5, y - 1], fill=(255, 40, 40))
    img.save(os.path.join(ART, f"st{n}_preview.png"))


def pal_grid(p, w=512, h=224):
    return [[p] * (w // 8) for _ in range(h // 8)]


def set_pal_rect(grid, x0, y0, x1, y1, p):
    for ty in range(y0 // 8, (y1 + 7) // 8):
        for tx in range(x0 // 8, (x1 + 7) // 8):
            if 0 <= ty < len(grid) and 0 <= tx < len(grid[0]):
                grid[ty][tx] = p
