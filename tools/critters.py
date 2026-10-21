"""Generates the FFA stage enemy (a billy goat) plus the grape projectile and
hit sparks. They share one 16-colour sprite palette.

Output:
  art/sprites/goat.png   32 x (32 * 4)   walk0, walk1, charge, hurt
  art/sprites/small.png  16 x (16 * 6)   grape0, grape1, spark0, spark1, spark2, heart
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, capsule, ellipse, shade, outlined, to_image, snes_color

OUT = os.path.join(os.path.dirname(__file__), "..", "art", "sprites")

PAL = [(255, 0, 255), (20, 16, 28),
       (244, 240, 228), (204, 198, 186), (148, 140, 134),   # 2,3,4 goat fur
       (176, 140, 100), (120, 92, 68),                      # 5,6 horn light/dark
       (232, 150, 150),                                     # 7 nose / ear pink
       (72, 56, 56),                                        # 8 hooves
       (232, 200, 64),                                      # 9 eye / spark yellow
       (184, 112, 216), (128, 64, 168), (78, 32, 108),      # 10,11,12 grape
       (96, 176, 72),                                       # 13 stem green
       (255, 255, 255),                                     # 14 white
       (232, 64, 64)]                                       # 15 red (heart)


def goat(frame):
    layers = []
    walk = {"walk0": 0, "walk1": 1, "charge": 2, "hurt": 3}[frame]
    head_drop = 4 if frame == "charge" else 0
    lean = -2 if frame == "hurt" else 0

    # far legs
    far = Canvas(32, 32)
    swing = [2, -2, 4, 0][walk]
    capsule(far, (10, 20), (10 - swing, 29), 1.1, 4)
    capsule(far, (21, 20), (21 + swing, 29), 1.1, 4)
    layers.append(far)

    body = Canvas(32, 32)
    ellipse(body, 15 + lean, 16, 10, 6, 3)
    shade(body, 3, 2, 4)
    # shaggy belly tufts
    for x in range(9, 22, 3):
        body.set(x + lean, 22, 3)
    ellipse(body, 6 + lean, 14, 1.5, 1.2, 3)   # tail
    layers.append(body)

    near = Canvas(32, 32)
    capsule(near, (12, 20), (12 + swing, 29), 1.2, 3)
    capsule(near, (19, 20), (19 - swing, 29), 1.2, 3)
    shade(near, 3, 2, 4)
    for x in (12 + swing, 19 - swing):
        near.set(x - 1, 29, 8); near.set(x, 29, 8); near.set(x + 1, 29, 8)
    far_hooves = [(10 - swing, 29), (21 + swing, 29)]
    for hx, hy in far_hooves:
        far.set(hx, hy, 8); far.set(hx + 1, hy, 8)
    layers.append(near)

    head = Canvas(32, 32)
    hx, hy = 24 + lean, 11 + head_drop
    capsule(head, (22 + lean, 15), (hx, hy), 2.6, 3)                 # neck
    ellipse(head, hx + 2, hy, 3.6, 3.0, 2)                           # skull
    capsule(head, (hx + 2, hy + 1), (hx + 6, hy + 2), 1.8, 2)        # muzzle
    shade(head, 2, None, 3)
    head.set(hx + 7, hy + 1, 7)                                      # nose
    capsule(head, (hx + 3, hy + 4), (hx + 3, hy + 6), 0.8, 3)        # beard
    head.set(hx + 2, hy - 1, 9); head.set(hx + 3, hy - 1, 1)         # eye
    ellipse(head, hx - 1, hy - 1, 1.8, 1.0, 7)                       # ear
    layers.append(head)

    horn = Canvas(32, 32)
    pts = [(hx + 1, hy - 2), (hx - 1, hy - 5), (hx - 4, hy - 5), (hx - 5, hy - 3)]
    if frame == "charge":   # horns forward
        pts = [(hx + 2, hy - 2), (hx + 4, hy - 4), (hx + 7, hy - 4)]
    for a, b in zip(pts, pts[1:]):
        capsule(horn, a, b, 1.1, 5)
    shade(horn, 5, None, 6)
    layers.append(horn)

    out = Canvas(32, 32)
    for layer in layers:
        out.blit(outlined(layer, 1))
    if frame == "hurt":   # flash: swap fur for white
        for y in range(32):
            for x in range(32):
                if out.px[y][x] in (3, 4):
                    out.px[y][x] = 14
    return out


def grape(spin):
    c = Canvas(16, 16)
    ellipse(c, 8, 9, 3.4, 3.4, 11)
    shade(c, 11, 10, 12)
    c.set(7, 7, 14)
    stem = [(8, 5), (9, 4)] if spin == 0 else [(10, 7), (11, 6)]
    for x, y in stem:
        c.set(x, y, 13)
    return outlined(c, 1)


def spark(n):
    c = Canvas(16, 16)
    r = [3, 6, 7][n]
    for i in range(8):
        a = i * math.pi / 4 + (0.4 if n == 1 else 0)
        inner = r * 0.4
        x0, y0 = 8 + math.cos(a) * inner, 8 + math.sin(a) * inner
        x1, y1 = 8 + math.cos(a) * r, 8 + math.sin(a) * r
        if n < 2 or i % 2 == 0:
            capsule(c, (x0, y0), (x1, y1), 0.7, 9 if n < 2 else 14)
    if n == 0:
        ellipse(c, 8, 8, 2, 2, 14)
    return c


HEART = [
    "................",
    "................",
    "................",
    "...ooo...ooo....",
    "..oRRRo.oRRRo...",
    ".oRWRRRoRRRRRo..",
    ".oRWRRRRRRRRRo..",
    ".oRRRRRRRRRRRo..",
    "..oRRRRRRRRRo...",
    "...oRRRRRRRo....",
    "....oRRRRRo.....",
    ".....oRRRo......",
    "......oRo.......",
    ".......o........",
    "................",
    "................",
]


def heart():
    from pixel import ascii_canvas
    return ascii_canvas(HEART, {"o": 1, "R": 15, "W": 14})


def main():
    pal = [snes_color(c) for c in PAL]
    sheet = Canvas(32, 32 * 4)
    for i, f in enumerate(["walk0", "walk1", "charge", "hurt"]):
        sheet.blit(goat(f), 0, 32 * i)
    to_image(sheet, pal).save(os.path.join(OUT, "goat.png"))

    small = Canvas(16, 16 * 6)
    for i, c in enumerate([grape(0), grape(1), spark(0), spark(1), spark(2), heart()]):
        small.blit(c, 0, 16 * i)
    to_image(small, pal).save(os.path.join(OUT, "small.png"))


if __name__ == "__main__":
    main()
