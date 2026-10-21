"""Composes the title / character select BG1 tilemap.

BG1 VRAM holds the stage tiles from tile 0 and the logo tiles from tile
LOGO_BASE, so the title can show the logo above the real arena floor.
Also writes dimmed hero palettes used for the unselected friend.
"""
import os
import struct

ROOT = os.path.join(os.path.dirname(__file__), "..")
BUILD = os.path.join(ROOT, "build")
LOGO_BASE = 256
LOGO_PAL = 3


def read_words(name):
    data = open(os.path.join(BUILD, name), "rb").read()
    return list(struct.unpack("<%dH" % (len(data) // 2), data))


def main():
    dims = dict(line.split()[1:] for line in open(os.path.join(BUILD, "logo_dims.h")))
    lw, lh = int(dims["LOGO_W"]), int(dims["LOGO_H"])
    logo = read_words("logo.map")
    m16 = read_words("st1.m16")
    t16 = read_words("st1.t16")
    sw = m16[0] // 8
    grid = m16[3:]
    tmap = [0] * (32 * 32)
    for y in range(28):          # bottom rows: the arena floor from the stage
        if y < 22:
            continue
        for x in range(32):
            tmap[y * 32 + x] = t16[grid[y * sw + x]] & 0x3FFF
    ox, oy = (32 - lw) // 2, 2
    for y in range(lh):
        for x in range(lw):
            t = logo[y * lw + x]
            if t:
                tmap[(oy + y) * 32 + ox + x] = (LOGO_BASE + t) | (LOGO_PAL << 10)
    # BG1 map is 64x32 (map engine layout); title only uses the left screen
    full = tmap + [0] * (32 * 32)
    open(os.path.join(BUILD, "title_bg1.map"), "wb").write(struct.pack("<%dH" % len(full), *full))

    for hero in ("jon", "wes"):
        pal = read_words(f"{hero}.pal")
        dim = []
        for i, c in enumerate(pal):
            r, g, b = c & 31, (c >> 5) & 31, (c >> 10) & 31
            if i > 1:
                r, g, b = r * 5 // 10, g * 5 // 10, (b * 5 + 31 * 1) // 10
            dim.append(r | (g << 5) | (b << 10))
        open(os.path.join(BUILD, f"{hero}_dim.pal"), "wb").write(struct.pack("<16H", *dim))


if __name__ == "__main__":
    main()
