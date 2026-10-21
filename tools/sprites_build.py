"""Converts the generated sprite sheets into the VRAM layout used by
PVSnesLib's dynamic sprite engine (frames on a 128px wide grid).

Heroes and beasts are 32x32 frames (one large sprite each); grapes, sparks,
hearts and chickens are 16x16 frames.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image
from snesgfx import tile_4bpp, palette_bytes

ROOT = os.path.join(os.path.dirname(__file__), "..")
SPR = os.path.join(ROOT, "art", "sprites")
BUILD = os.path.join(ROOT, "build")


def load(name):
    im = Image.open(os.path.join(SPR, name))
    w, h = im.size
    data = list(im.getdata()) if not hasattr(im, "get_flattened_data") else list(im.get_flattened_data())
    rows = [data[y * w:(y + 1) * w] for y in range(h)]
    pal = im.getpalette()[:48]
    colors = [tuple(pal[i * 3:i * 3 + 3]) for i in range(16)]
    return rows, w, h, colors


def grid_pic(frames, size):
    """frames: list of size x size index grids. Lay them out size-per-cell on a
    128px wide grid and return 4bpp tile data in row-major tile order."""
    per_row = 128 // size
    nrows = (len(frames) + per_row - 1) // per_row
    canvas = [[0] * 128 for _ in range(nrows * size)]
    for i, f in enumerate(frames):
        ox, oy = (i % per_row) * size, (i // per_row) * size
        for y in range(size):
            for x in range(size):
                canvas[oy + y][ox + x] = f[y][x]
    out = bytearray()
    for ty in range(len(canvas) // 8):
        for tx in range(16):
            out += tile_4bpp([canvas[ty * 8 + y][tx * 8:(tx + 1) * 8] for y in range(8)])
    return bytes(out)


def frames_of(rows, w, fh):
    return [[rows[i * fh + y][:w] for y in range(fh)] for i in range(len(rows) // fh)]


def main():
    os.makedirs(BUILD, exist_ok=True)
    for hero in ("jon", "wes"):
        rows, w, h, colors = load(f"{hero}.png")
        open(os.path.join(BUILD, f"{hero}.pic"), "wb").write(grid_pic(frames_of(rows, 32, 32), 32))
        open(os.path.join(BUILD, f"{hero}.pal"), "wb").write(palette_bytes(colors))

if __name__ == "__main__":
    main()
