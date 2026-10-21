"""Pickups, checkpoint flags, weapon shots and breakable props (16x16, sprite palette 3).

Writes build/items.pic + build/items.pal and art/sprites/items.png.

Frames (see the IF_* defines in src/game.h):
   0      checkpoint flag lowered
   1-2    checkpoint flag raised, waving
   3      extra life (1UP)
   4-5    star (points), spinning
   6-9    weapon pickups: spread, rapid, boomerang, bomb
  10-11   rapid bolt
  12-13   boomerang pick, spinning
  14-15   bomb, fuse sparking
  16-18   explosion
  19-30   breakable props, two frames per stage (whole, cracked):
          feed crate, record box, trash can, cooler, file box, gift box
  31-32   score popup sparkle
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, capsule, ellipse, shade, outlined, to_image, snes_color
from snesgfx import palette_bytes
from sprites_build import grid_pic
from stagekit import fill, frame_box

ROOT = os.path.join(os.path.dirname(__file__), "..")
BUILD = os.path.join(ROOT, "build")
SPR = os.path.join(ROOT, "art", "sprites")

OUT, WHITE, LGRAY, DGRAY = 1, 2, 3, 4
RED, DRED, YEL, ORG = 5, 6, 7, 8
BRN, DBRN, GRN, DGRN = 9, 10, 11, 12
BLUE, CYAN, TAN = 13, 14, 15
PAL = [(255, 0, 255), (24, 18, 30), (248, 248, 240), (176, 180, 192), (96, 96, 112),
       (224, 48, 48), (136, 24, 36), (252, 220, 64), (244, 140, 36),
       (184, 120, 60), (112, 66, 34), (80, 196, 80), (32, 112, 52),
       (64, 120, 232), (128, 208, 252), (236, 200, 150)]


def outline(c):
    return outlined(c, OUT)


def flag(state, wave=0):
    c = Canvas(16, 16)
    fill(c, 3, 1, 5, 16, LGRAY)
    c.set(3, 1, WHITE)
    for y in range(1, 16):
        c.set(4, y, DGRAY)
    ellipse(c, 4, 1, 1.3, 1.3, YEL)
    if state == 0:
        # lowered: a grey pennant drooping at the foot of the pole
        for y in range(10, 15):
            for x in range(5, 5 + (15 - y)):
                c.set(x, y, DGRAY)
    else:
        for y in range(2, 9):
            off = int(round(math.sin((y + wave * 2) * 0.9)))
            for x in range(5, 14):
                yy = y + (off if x > 8 else 0)
                c.set(x, yy, RED if (x + y) % 5 else DRED)
        # a little star on the flag
        c.set(9, 5, YEL); c.set(8, 5, YEL); c.set(10, 5, YEL); c.set(9, 4, YEL); c.set(9, 6, YEL)
    return outline(c)


def oneup():
    c = Canvas(16, 16)
    ellipse(c, 8, 8, 6.6, 6.6, GRN)
    shade(c, GRN, None, DGRN)
    # "1UP"
    glyphs = {"1": ["010", "110", "010", "010", "111"], "U": ["101", "101", "101", "101", "111"],
              "P": ["110", "101", "110", "100", "100"]}
    x = 2
    for ch in "1UP":
        for yy, row in enumerate(glyphs[ch]):
            for xx, v in enumerate(row):
                if v == "1":
                    c.set(x + xx, 6 + yy, WHITE)
        x += 4
    return outline(c)


def star(phase):
    c = Canvas(16, 16)
    w = [1.0, 0.45][phase]
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        r = 6.5 if k % 2 == 0 else 2.8
        pts.append((8 + math.cos(a) * r * w, 8.5 - math.sin(a) * r))
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5, y + 0.5
            inside = False
            j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi:
                    inside = not inside
                j = i
            if inside:
                c.set(x, y, YEL)
    shade(c, YEL, WHITE, ORG)
    return outline(c)


def badge(color, dark, draw):
    """Weapon pickup: a round badge with an icon."""
    c = Canvas(16, 16)
    ellipse(c, 8, 8, 6.8, 6.8, color)
    shade(c, color, None, dark)
    draw(c)
    return outline(c)


def icon_spread(c):
    for a in (-30, 0, 30):
        r = math.radians(a)
        for t in range(3):
            x = 5 + t * 2 * math.cos(r)
            y = 8 - t * 2 * math.sin(r)
            c.set(int(x), int(y), WHITE)
        ellipse(c, 5 + 6 * math.cos(r), 8 - 6 * math.sin(r) + 0.3, 1.2, 1.2, YEL)


def icon_rapid(c):
    pts = [(10, 3), (6, 8), (9, 8), (6, 13)]
    for a, b in zip(pts, pts[1:]):
        capsule(c, a, b, 0.8, YEL)


def icon_rang(c):
    capsule(c, (4.5, 5), (8, 9), 1.2, WHITE)
    capsule(c, (8, 9), (12, 5), 1.2, WHITE)


def icon_bomb(c):
    ellipse(c, 7.5, 9, 3.6, 3.6, OUT)
    c.set(6, 8, DGRAY)
    capsule(c, (10, 6), (12, 3.5), 0.5, BRN)
    c.set(12, 3, YEL)


def bolt(phase):
    c = Canvas(16, 16)
    capsule(c, (3, 8), (13, 8), 1.6, YEL)
    capsule(c, (5, 8), (13, 8), 0.7, WHITE)
    if phase:
        c.set(2, 6, ORG); c.set(1, 10, ORG)
    else:
        c.set(2, 10, ORG); c.set(1, 6, ORG)
    return outline(c)


def rang(phase):
    c = Canvas(16, 16)
    # a big guitar pick spinning: rounded triangle, seen flat or edge-on
    if phase == 0:
        pts = [(8, 13), (2.5, 4), (13.5, 4)]
        for y in range(16):
            for x in range(16):
                px, py = x + 0.5, y + 0.5
                # inside the triangle, softened by distance to the centroid
                d = math.hypot(px - 8, py - 7)
                if d < 6.2 and py > 2.5 and abs(px - 8) < (13.5 - py) * 0.62 + 1.5:
                    c.set(x, y, ORG)
        shade(c, ORG, YEL, DRED)
        c.set(7, 6, WHITE)
    else:
        capsule(c, (3, 8), (13, 8), 1.8, ORG)
        shade(c, ORG, YEL, DRED)
    return outline(c)


def bomb(phase):
    c = Canvas(16, 16)
    ellipse(c, 7.5, 9.5, 4.8, 4.8, DGRAY)
    shade(c, DGRAY, LGRAY, OUT)
    c.set(5, 7, WHITE)
    capsule(c, (10.5, 5.5), (12, 3), 0.6, BRN)
    if phase:
        c.set(12, 2, YEL); c.set(13, 1, ORG); c.set(11, 1, YEL); c.set(13, 3, WHITE)
    else:
        c.set(12, 2, WHITE); c.set(13, 2, YEL)
    return outline(c)


def boom(phase):
    """The top-left quarter of a 32x32 blast; the game mirrors it four ways."""
    c = Canvas(16, 16)
    cx = cy = 16
    r = [7.5, 12.5, 15.0][phase]
    ellipse(c, cx, cy, r, r, ORG if phase < 2 else DGRAY)
    ellipse(c, cx, cy, r * 0.7, r * 0.7, YEL if phase < 2 else LGRAY)
    if phase < 2:
        ellipse(c, cx, cy, r * 0.35, r * 0.35, WHITE)
    for k in range(5):
        a = math.pi + k * (math.pi / 2) / 4 + phase * 0.3
        for d in (r + 0.5, r - 0.5):
            x = cx + math.cos(a) * d
            y = cy + math.sin(a) * d
            if 0 <= x < 16 and 0 <= y < 16:
                c.set(int(x), int(y), RED if phase < 2 else DGRAY)
    if phase == 2:
        # the smoke breaks up into puffs drifting outwards
        c = Canvas(16, 16)
        for a, d, pr in ((3.5, 10, 4.2), (3.95, 6, 3.6), (4.45, 11, 4.0), (4.0, 13.5, 2.6), (3.3, 13, 2.4)):
            x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
            ellipse(c, x, y, pr, pr, DGRAY)
            ellipse(c, x - 0.8, y - 0.8, pr * 0.6, pr * 0.6, LGRAY)
    return c


def cracked(c, seed):
    """Add a jagged crack across a prop."""
    x, y = 4 + seed % 5, 3
    while y < 14:
        c.set(x, y, OUT)
        x += (1 if (x + y + seed) % 3 == 0 else (-1 if (x * y + seed) % 4 == 0 else 0))
        y += 1
    return c


def crate(colour, dark, light):
    c = Canvas(16, 16)
    fill(c, 1, 2, 15, 16, colour)
    frame_box(c, 1, 2, 15, 16, dark)
    frame_box(c, 2, 3, 14, 15, dark)
    capsule(c, (3, 4), (12, 13), 0.6, dark)
    for x in range(3, 13):
        c.set(x, 3, light)
    return c


def prop(stage):
    """Each stage's breakable, whole."""
    c = Canvas(16, 16)
    if stage == 0:      # feed crate with a ? stencil
        c = crate(BRN, DBRN, TAN)
        fill(c, 5, 5, 11, 13, BRN)
        for p in ((6, 6), (7, 5), (8, 5), (9, 5), (10, 6), (10, 7), (9, 8), (8, 9), (8, 11)):
            c.set(*p, YEL)
    elif stage == 1:    # cardboard box of records
        fill(c, 1, 4, 15, 16, TAN)
        fill(c, 1, 4, 15, 6, BRN)
        frame_box(c, 1, 4, 15, 16, DBRN)
        ellipse(c, 5, 3.5, 3, 1.6, OUT)
        ellipse(c, 10, 3, 3, 1.6, OUT)
        c.set(5, 3, RED); c.set(10, 3, BLUE)
        fill(c, 6, 9, 10, 11, DBRN)
    elif stage == 2:    # dented trash can
        fill(c, 3, 4, 13, 16, LGRAY)
        fill(c, 2, 3, 14, 5, DGRAY)
        for x in (5, 8, 11):
            for y in range(6, 15):
                c.set(x, y, DGRAY)
        fill(c, 7, 1, 9, 3, DGRAY)
        shade(c, LGRAY, WHITE, DGRAY)
    elif stage == 3:    # cooler
        fill(c, 1, 5, 15, 16, BLUE)
        fill(c, 1, 4, 15, 7, WHITE)
        fill(c, 5, 2, 11, 4, DGRAY)
        shade(c, BLUE, CYAN, OUT)
        fill(c, 3, 9, 7, 11, WHITE)
    elif stage == 4:    # file box
        fill(c, 1, 4, 15, 16, TAN)
        frame_box(c, 1, 4, 15, 16, DBRN)
        fill(c, 1, 4, 15, 7, BRN)
        fill(c, 6, 9, 10, 11, WHITE)
        fill(c, 3, 2, 13, 4, WHITE)
        c.set(5, 2, LGRAY); c.set(9, 2, LGRAY)
    else:               # gift box
        fill(c, 1, 5, 15, 16, RED)
        fill(c, 7, 5, 9, 16, YEL)
        fill(c, 1, 9, 15, 11, YEL)
        ellipse(c, 6, 3.5, 2.2, 1.5, YEL)
        ellipse(c, 10, 3.5, 2.2, 1.5, YEL)
        shade(c, RED, None, DRED)
    return c


def sparkle(phase):
    c = Canvas(16, 16)
    r = 3 + phase * 2
    for k in range(4):
        a = k * math.pi / 2 + phase * math.pi / 4
        capsule(c, (8, 8), (8 + math.cos(a) * r, 8 + math.sin(a) * r), 0.5, YEL if phase == 0 else WHITE)
    c.set(8, 8, WHITE)
    return c


def frames():
    out = [flag(0), flag(1, 0), flag(1, 1), oneup(), star(0), star(1),
           badge(ORG, DRED, icon_spread), badge(BLUE, OUT, icon_rapid),
           badge(GRN, DGRN, icon_rang), badge(RED, DRED, icon_bomb),
           bolt(0), bolt(1), rang(0), rang(1), bomb(0), bomb(1), boom(0), boom(1), boom(2)]
    for s in range(6):
        whole = outline(prop(s))
        out += [whole, cracked(whole.copy(), s)]
    out += [sparkle(0), sparkle(1)]
    return out


def main():
    os.makedirs(BUILD, exist_ok=True)
    fr = frames()
    assert len(fr) == 33
    open(os.path.join(BUILD, "items.pic"), "wb").write(grid_pic([f.px for f in fr], 16))
    open(os.path.join(BUILD, "items.pal"), "wb").write(palette_bytes(PAL))
    sheet = Canvas(16 * 8, 16 * ((len(fr) + 7) // 8))
    for i, f in enumerate(fr):
        sheet.blit(f, (i % 8) * 16, (i // 8) * 16)
    to_image(sheet, [snes_color(p) for p in PAL]).save(os.path.join(SPR, "items.png"))
    print("items written")


if __name__ == "__main__":
    main()
