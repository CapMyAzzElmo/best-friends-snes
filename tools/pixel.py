"""Small pixel-art toolkit used by the sprite and background generators.

Images are lists of rows of palette indices; 0 is transparent.
"""
import math
from PIL import Image


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [[0] * w for _ in range(h)]

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return 0

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def filled(self, x, y):
        return self.get(x, y) != 0

    def blit(self, other, ox=0, oy=0, flip=False):
        for y in range(other.h):
            for x in range(other.w):
                c = other.px[y][other.w - 1 - x if flip else x]
                if c:
                    self.set(x + ox, y + oy, c)

    def copy(self):
        c = Canvas(self.w, self.h)
        c.px = [row[:] for row in self.px]
        return c

    def shifted(self, dx, dy):
        c = Canvas(self.w, self.h)
        c.blit(self, dx, dy)
        return c


def ascii_canvas(rows, legend):
    w = max(len(r) for r in rows)
    c = Canvas(w, len(rows))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in legend:
                c.px[y][x] = legend[ch]
    return c


def capsule(c, p0, p1, r, color):
    """Fill every pixel whose centre lies within r of the segment p0-p1."""
    (x0, y0), (x1, y1) = p0, p1
    minx, maxx = int(min(x0, x1) - r - 1), int(max(x0, x1) + r + 2)
    miny, maxy = int(min(y0, y1) - r - 1), int(max(y0, y1) + r + 2)
    dx, dy = x1 - x0, y1 - y0
    ll = dx * dx + dy * dy
    for y in range(miny, maxy):
        for x in range(minx, maxx):
            px, py = x + 0.5, y + 0.5
            t = 0 if ll == 0 else max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / ll))
            qx, qy = x0 + t * dx, y0 + t * dy
            if (px - qx) ** 2 + (py - qy) ** 2 <= r * r:
                c.set(x, y, color)


def ellipse(c, cx, cy, rx, ry, color):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                c.set(x, y, color)


def shade(c, mid, light, dark, light_dirs=((-1, 0), (0, -1)), dark_dirs=((1, 0), (0, 1))):
    """Edge shading: light from the upper left, shadow on the lower right."""
    out = c.copy()
    for y in range(c.h):
        for x in range(c.w):
            if c.px[y][x] != mid:
                continue
            if any(not c.filled(x + dx, y + dy) for dx, dy in dark_dirs):
                out.px[y][x] = dark
            elif light is not None and any(not c.filled(x + dx, y + dy) for dx, dy in light_dirs):
                out.px[y][x] = light
    c.px = out.px


def outlined(c, color):
    """Return a canvas holding the part plus a 1px outline ring around it."""
    out = c.copy()
    for y in range(c.h):
        for x in range(c.w):
            if c.px[y][x]:
                continue
            if any(c.filled(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.px[y][x] = color
    return out


def to_image(c, palette):
    img = Image.new("P", (c.w, c.h))
    flat = []
    for rgb in palette:
        flat.extend(rgb)
    flat.extend([0] * (768 - len(flat)))
    img.putpalette(flat)
    img.putdata([v for row in c.px for v in row])
    return img


def snes_color(rgb):
    """Snap an 8-bit colour to the SNES 15-bit grid so previews match hardware."""
    return tuple((v >> 3) << 3 for v in rgb)


def rot(p, ang, length):
    """Point at `length` from p, `ang` degrees from straight down, positive = towards facing (right)."""
    a = math.radians(ang)
    return (p[0] + math.sin(a) * length, p[1] + math.cos(a) * length)
