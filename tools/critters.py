"""Generates the FFA stage critters plus the grape projectile, hit sparks and
heart pickup.

  art/sprites/beasts.png  32x32 frames: goat walk0-3, goat charge0-1, goat hurt,
                          pig walk0-3, pig charge0-1, pig hurt
                          (goat uses the critter palette, the pig its own palette
                          with the same index layout)
  art/sprites/small.png   16x16 frames: grape0-1, spark0-2, heart,
                          chicken walk0-1, flap0-1, hurt
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, ascii_canvas, capsule, ellipse, shade, outlined, to_image, snes_color

OUT = os.path.join(os.path.dirname(__file__), "..", "art", "sprites")

PAL = [(255, 0, 255), (20, 16, 28),
       (244, 240, 228), (204, 198, 186), (148, 140, 134),   # 2,3,4 fur / feathers
       (176, 140, 100), (120, 92, 68),                      # 5,6 horn light/dark
       (232, 150, 150),                                     # 7 nose / ear pink
       (72, 56, 56),                                        # 8 hooves
       (240, 196, 56),                                      # 9 yellow: eyes, beak, sparks
       (184, 112, 216), (128, 64, 168), (78, 32, 108),      # 10,11,12 grape
       (96, 176, 72),                                       # 13 stem green
       (255, 255, 255),                                     # 14 white
       (224, 56, 56)]                                       # 15 red: heart, comb

PIG_PAL = [(255, 0, 255), (28, 14, 22),
           (252, 204, 200), (234, 150, 156), (180, 94, 110),  # 2,3,4 pink body
           (124, 86, 58), (86, 58, 40),                       # 5,6 mud
           (210, 112, 128),                                   # 7 snout
           (70, 46, 46),                                      # 8 hooves
           (240, 196, 56),
           (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
           (255, 255, 255),
           (224, 56, 56)]


def beast(kind, frame):
    """kind: goat or pig. frame: walk0-3, charge0-1, hurt."""
    goat = kind == "goat"
    walk = frame.startswith("walk")
    i = int(frame[-1]) if frame[-1].isdigit() else 0
    charge = frame.startswith("charge")
    hurt = frame == "hurt"
    layers = []
    ground = 30
    body_y = 20 if goat else 21
    rx, ry = (8.0, 4.6) if goat else (10.0, 6.2)
    cx = 15
    lean = -2 if hurt else 0
    leg_len = 7 if goat else 5
    bob = 1 if (walk and i in (1, 3)) or (charge and i == 1) else 0
    by = body_y + bob

    # gait: diagonal pairs swing together
    if walk:
        sw = [3, 0, -3, 0][i]
    elif charge:
        sw = [4, -4][i]
    else:
        sw = 0
    hips = [(cx - rx + 3, "far", sw), (cx + rx - 3, "far", -sw), (cx - rx + 4, "near", -sw), (cx + rx - 2, "near", sw)]
    far, near = Canvas(32, 32), Canvas(32, 32)
    for hx, which, s in hips:
        c = far if which == "far" else near
        hx += lean
        capsule(c, (hx, by + 2), (hx + s * 0.6, ground - 1), 1.0 if goat else 1.4, 4 if which == "far" else 3)
        c.set(int(hx + s * 0.6), ground - 1, 8)
        c.set(int(hx + s * 0.6) + 1, ground - 1, 8)
    shade(near, 3, 2, 4)
    layers.append(far)

    body = Canvas(32, 32)
    ellipse(body, cx + lean, by, rx, ry, 3)
    shade(body, 3, 2, 4)
    if goat:
        for x in range(int(cx - rx + 3), int(cx + rx - 1), 3):
            body.set(x + lean, int(by + ry), 3)          # shaggy belly
        ellipse(body, cx - rx + 1 + lean, by - 3, 1.2, 1.0, 3)   # tail
    else:
        for (sx, sy) in ((cx - 3, by - 2), (cx + 3, by + 1), (cx - 6, by + 2)):
            ellipse(body, sx + lean, sy, 1.5, 1.0, 5)    # mud spots
        capsule(body, (cx - rx + lean, by - 2), (cx - rx - 1.5 + lean, by - 4), 0.6, 4)  # curly tail
    layers.append(body)
    layers.append(near)

    head = Canvas(32, 32)
    drop = 3 if charge else 0
    if goat:
        hx, hy = cx + rx - 1 + lean, by - 6 + drop
        capsule(head, (cx + rx - 4 + lean, by - 1), (hx, hy + 1), 2.0, 3)
        ellipse(head, hx + 1.5, hy, 2.8, 2.4, 2)
        capsule(head, (hx + 2, hy + 1), (hx + 5, hy + 1.5), 1.4, 2)
        shade(head, 2, None, 3)
        head.set(int(hx + 5), int(hy + 1), 7)
        capsule(head, (hx + 2.5, hy + 3), (hx + 2.5, hy + 5), 0.6, 3)   # beard
        head.set(int(hx + 1), int(hy - 1), 9)
        head.set(int(hx + 2), int(hy - 1), 1)
        ellipse(head, hx - 1.5, hy - 1, 1.4, 0.8, 7)
    else:
        hx, hy = cx + rx - 2 + lean, by - 2 + drop
        ellipse(head, hx + 1, hy, 4.2, 3.8, 3)
        shade(head, 3, 2, 4)
        ellipse(head, hx + 5, hy + 1, 1.6, 2.0, 7)      # snout
        head.set(int(hx + 5), int(hy + 1), 1)
        head.set(int(hx + 1), int(hy - 2), 1)           # eye
        capsule(head, (hx - 1, hy - 3), (hx - 2.5, hy - 6), 1.0, 4)  # ear
    layers.append(head)

    if goat:
        horn = Canvas(32, 32)
        if charge:
            pts = [(hx + 1, hy - 2), (hx + 3, hy - 3.5), (hx + 6, hy - 3.5)]
        else:
            pts = [(hx + 1, hy - 2), (hx - 0.5, hy - 4.5), (hx - 3, hy - 4.5), (hx - 4, hy - 2.5)]
        for a, b in zip(pts, pts[1:]):
            capsule(horn, a, b, 0.8, 5)
        shade(horn, 5, None, 6)
        layers.append(horn)

    out = Canvas(32, 32)
    for layer in layers:
        out.blit(outlined(layer, 1))
    if hurt:   # flash white
        for y in range(32):
            for x in range(32):
                if out.px[y][x] in (3, 4, 5, 7):
                    out.px[y][x] = 14 if goat else 2
    if charge and i == 1:   # dust puffs behind the charge
        for (dx, dy) in ((2, 29), (4, 28), (1, 27)):
            out.set(dx, dy, 3 if goat else 2)
    return out


def chicken(frame):
    c = Canvas(16, 16)
    walk = frame.startswith("walk")
    flap = frame.startswith("flap")
    i = int(frame[-1]) if frame[-1].isdigit() else 0
    legs = Canvas(16, 16)
    if not flap:
        s = [1, -1][i] if walk else 0
        capsule(legs, (7, 11), (7 + s, 14), 0.5, 9)
        capsule(legs, (9, 11), (9 - s, 14), 0.5, 9)
    else:
        capsule(legs, (7, 11), (6, 13), 0.5, 9)
        capsule(legs, (9, 11), (10, 13), 0.5, 9)
    body = Canvas(16, 16)
    ellipse(body, 8, 9, 4.2, 3.2, 3)
    capsule(body, (4, 8), (2.5, 5), 1.2, 3)            # tail
    ellipse(body, 11, 5, 2.2, 2.2, 3)                  # head
    shade(body, 3, 2, 4)
    body.set(13, 5, 9); body.set(14, 5, 9); body.set(13, 6, 9)   # beak
    body.set(11, 2, 15); body.set(12, 2, 15); body.set(11, 3, 15)  # comb
    body.set(12, 7, 15)                                # wattle
    body.set(12, 4, 1)                                 # eye
    wing = Canvas(16, 16)
    if flap:
        pts = [(7, 8), (4, 4 + i * 2)]
    else:
        pts = [(6, 9), (9, 9)]
    capsule(wing, pts[0], pts[1], 1.4, 2)
    out = Canvas(16, 16)
    for layer in (legs, body, wing):
        out.blit(outlined(layer, 1))
    if frame == "hurt":
        for y in range(16):
            for x in range(16):
                if out.px[y][x] in (3, 4):
                    out.px[y][x] = 14
    return out


def grape(spin):
    c = Canvas(16, 16)
    ellipse(c, 8, 9, 2.6, 2.6, 11)
    shade(c, 11, 10, 12)
    c.set(7, 8, 14)
    for x, y in ([(8, 6), (9, 5)] if spin == 0 else [(10, 7), (11, 6)]):
        c.set(x, y, 13)
    return outlined(c, 1)


def spark(n):
    c = Canvas(16, 16)
    r = [3, 5.5, 7][n]
    for k in range(8):
        a = k * math.pi / 4 + (0.4 if n == 1 else 0)
        x0, y0 = 8 + math.cos(a) * r * 0.4, 8 + math.sin(a) * r * 0.4
        x1, y1 = 8 + math.cos(a) * r, 8 + math.sin(a) * r
        if n < 2 or k % 2 == 0:
            capsule(c, (x0, y0), (x1, y1), 0.6, 9 if n < 2 else 14)
    if n == 0:
        ellipse(c, 8, 8, 1.8, 1.8, 14)
    return c


HEART = [
    "................",
    "................",
    "................",
    "................",
    "...ooo..ooo.....",
    "..oRWRooRRRo....",
    "..oRRRRRRRRo....",
    "..oRRRRRRRRo....",
    "...oRRRRRRo.....",
    "....oRRRRo......",
    ".....oRRo.......",
    "......oo........",
]


def main():
    pal = [snes_color(c) for c in PAL]
    frames = []
    for kind in ("goat", "pig"):
        for f in ["walk0", "walk1", "walk2", "walk3", "charge0", "charge1", "hurt"]:
            frames.append(beast(kind, f))
    sheet = Canvas(32, 32 * len(frames))
    for k, f in enumerate(frames):
        sheet.blit(f, 0, 32 * k)
    to_image(sheet, pal).save(os.path.join(OUT, "beasts.png"))
    # pig preview with its own palette
    to_image(sheet, [snes_color(c) for c in PIG_PAL]).save(os.path.join(OUT, "beasts_pigpal.png"))

    small = [grape(0), grape(1), spark(0), spark(1), spark(2),
             ascii_canvas(HEART + ["." * 16] * 4, {"o": 1, "R": 15, "W": 14}),
             chicken("walk0"), chicken("walk1"), chicken("flap0"), chicken("flap1"), chicken("hurt")]
    sh = Canvas(16, 16 * len(small))
    for k, f in enumerate(small):
        sh.blit(f, 0, 16 * k)
    to_image(sh, pal).save(os.path.join(OUT, "small.png"))


if __name__ == "__main__":
    main()
