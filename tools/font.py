"""Builds the 2bpp HUD/text font for BG3 and the title logo for BG1.

Font tiles follow ASCII from 0x20 (space) so text can be written directly:
tile = char - 0x20. Glyphs are 5x7 with a dark drop shadow.
Tile 0x60 onward hold HUD icons (full heart, empty heart).

Outputs build/font.pic (2bpp), build/logo.pic/.map (4bpp, BG palette 3),
and the shared CGRAM 0-15 colours in build/ui.pal.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image
from pixel import Canvas, outlined
from snesgfx import tile_4bpp, palette_bytes, words

ROOT = os.path.join(os.path.dirname(__file__), "..")
BUILD = os.path.join(ROOT, "build")

GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10011", "10101", "10101", "10101", "11001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    ".": ["00000", "00000", "00000", "00000", "00000", "00000", "00100"],
    ":": ["00000", "00100", "00000", "00000", "00000", "00100", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    ",": ["00000", "00000", "00000", "00000", "00000", "00100", "01000"],
    ">": ["01000", "01100", "01110", "01111", "01110", "01100", "01000"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "?": ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    "#": ["01010", "11111", "01010", "01010", "01010", "11111", "01010"],
}

HEART_FULL = ["01101100", "11111110", "11111110", "11111110", "01111100", "00111000", "00010000", "00000000"]

# UI colours: CGRAM 0-3 = BG3 palette 0 (text), 4-7 = BG3 palette 1 (hearts,
# bars), 8-11 = BG3 palette 2 (gold headings)
UI_PAL = [(14, 14, 26), (10, 8, 16), (248, 248, 240), (252, 208, 80),
          (0, 0, 0), (10, 8, 16), (232, 56, 64), (90, 90, 110),
          (0, 0, 0), (40, 20, 10), (252, 208, 80), (236, 140, 50)] + [(0, 0, 0)] * 4


def tile_2bpp(px):
    out = bytearray(16)
    for y in range(8):
        for x in range(8):
            v = px[y][x]
            out[y * 2] |= (v & 1) << (7 - x)
            out[y * 2 + 1] |= ((v >> 1) & 1) << (7 - x)
    return bytes(out)


def glyph_tile(rows, color=2, shadow=1):
    px = [[0] * 8 for _ in range(8)]
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "1":
                for dx, dy in ((1, 0), (0, 1), (1, 1)):
                    if px[y + dy][x + 1 + dx] == 0:
                        px[y + dy][x + 1 + dx] = shadow
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "1":
                px[y][x + 1] = color
    return px


def build_font():
    tiles = []
    for code in range(0x20, 0x60):
        ch = chr(code)
        if ch in GLYPHS:
            tiles.append(glyph_tile(GLYPHS[ch]))
        else:
            tiles.append([[0] * 8 for _ in range(8)])
    # 0x60: full heart (palette 1 colour 2 = red), 0x61: empty heart (colour 3 = grey)
    for col in (2, 3):
        px = [[0] * 8 for _ in range(8)]
        for y, r in enumerate(HEART_FULL):
            for x, ch in enumerate(r):
                if ch == "1":
                    px[y][x] = col
        # dark outline around the heart
        out = [row[:] for row in px]
        for y in range(8):
            for x in range(8):
                if px[y][x] == 0 and any(0 <= y + dy < 8 and 0 <= x + dx < 8 and px[y + dy][x + dx]
                                         for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    out[y][x] = 1
        tiles.append(out)
    # 0x42: full bar cell (red), 0x43: empty bar cell (grey)
    for col in (2, 3):
        px = [[0] * 8 for _ in range(8)]
        for y in range(1, 7):
            for x in range(0, 8):
                px[y][x] = 1 if y in (1, 6) else col
        tiles.append(px)
    with open(os.path.join(BUILD, "font.pic"), "wb") as f:
        for t in tiles:
            f.write(tile_2bpp(t))
    with open(os.path.join(BUILD, "ui.pal"), "wb") as f:
        f.write(palette_bytes(UI_PAL))


# --- title logo: chunky gold letters (each font pixel -> 3x3 block) ---------
LOGO_PAL = [(0, 0, 0), (22, 14, 20), (255, 244, 170), (252, 212, 90), (236, 168, 52),
            (196, 118, 34), (140, 70, 24), (60, 96, 196), (36, 60, 140), (244, 244, 236),
            (176, 52, 44), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
LOGO_PALNUM = 3


def logo_canvas(lines, scale=4):
    width = max(len(l) for l in lines) * 6 * scale + 8
    height = len(lines) * 9 * scale + 8
    width = (width + 7) // 8 * 8
    height = (height + 7) // 8 * 8
    c = Canvas(width, height)
    for li, text in enumerate(lines):
        x0 = (width - len(text) * 6 * scale) // 2 + 2
        y0 = 4 + li * 9 * scale
        for i, ch in enumerate(text):
            g = GLYPHS.get(ch)
            if not g:
                continue
            for gy, row in enumerate(g):
                for gx, bit in enumerate(row):
                    if bit != "1":
                        continue
                    for sy in range(scale):
                        for sx in range(scale):
                            y = gy * scale + sy
                            # vertical gold gradient across the glyph height
                            band = [2, 3, 3, 4, 4, 5, 5][min(6, y * 7 // (7 * scale))]
                            c.set(x0 + i * 6 * scale + gx * scale + sx, y0 + y, band)
    # thick dark outline plus a blue drop shadow
    o = outlined(c, 1)
    o = outlined(o, 1)
    shadow = Canvas(width, height)
    for y in range(height):
        for x in range(width):
            if o.px[y][x] and not o.get(x + 2, y + 2):
                shadow.set(x + 2, y + 2, 8)
    final = Canvas(width, height)
    final.blit(shadow)
    final.blit(o)
    return final


def build_logo():
    c = logo_canvas(["COMRADES"])
    tiles, index, tmap = [], {}, []
    tw, th = c.w // 8, c.h // 8
    blank = tuple(tuple([0] * 8) for _ in range(8))
    index[blank] = 0
    tiles.append(blank)
    for ty in range(th):
        for tx in range(tw):
            px = tuple(tuple(c.px[ty * 8 + y][tx * 8 + x] for x in range(8)) for y in range(8))
            if px not in index:
                index[px] = len(tiles)
                tiles.append(px)
            tmap.append(index[px])
    with open(os.path.join(BUILD, "logo.pic"), "wb") as f:
        for t in tiles:
            f.write(tile_4bpp(t))
    with open(os.path.join(BUILD, "logo.pal"), "wb") as f:
        f.write(palette_bytes(LOGO_PAL))
    print(f"logo: {tw}x{th} tiles, {len(tiles)} unique")
    with open(os.path.join(BUILD, "logo_dims.h"), "w") as f:
        f.write(f"#define LOGO_W {tw}\n#define LOGO_H {th}\n")
    with open(os.path.join(BUILD, "logo.map"), "wb") as f:
        f.write(words(tmap))
    snap = lambda rgb: tuple((v >> 3) << 3 for v in rgb)
    img = Image.new("RGB", (c.w, c.h))
    img.putdata([snap(LOGO_PAL[v]) if v else (40, 40, 60) for row in c.px for v in row])
    img.resize((c.w * 3, c.h * 3), Image.NEAREST).save(os.path.join(ROOT, "art", "bg", "logo_preview.png"))


if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True)
    build_font()
    build_logo()
