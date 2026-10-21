"""Checks that every stage can be crossed with the lower of the two heroes' jumps.

Reads the collision data the stage scripts export (build/stN.m16 + .b16) and
searches standing spots: walk, drop off ledges, and jump up to JUMP pixels
higher within a few tiles across. Prints the furthest point reached.
"""
import os
import struct
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
BUILD = os.path.join(ROOT, "build")
T_SOLID, T_PLATE = 0xFF00, 0x0008


def load(n):
    m = open(os.path.join(BUILD, f"st{n}.m16"), "rb").read()
    wpx, hpx, _ = struct.unpack_from("<3H", m, 0)
    W, H = wpx // 8, hpx // 8
    grid = struct.unpack_from(f"<{W * H}H", m, 6)
    b = open(os.path.join(BUILD, f"st{n}.b16"), "rb").read()
    attr = struct.unpack_from("<1024H", b, 0)
    col = [[attr[grid[y * W + x]] for x in range(W)] for y in range(H)]
    return W, H, col


def standable(W, H, col):
    """(tx, ty): hero stands on top of tile row ty in column tx (needs 4 free rows above)."""
    spots = set()
    for x in range(W):
        for y in range(1, H):
            if col[y][x] in (T_SOLID, T_PLATE) and col[y - 1][x] not in (T_SOLID, T_PLATE):
                if all(col[y - k][x] != T_SOLID for k in range(1, 5) if y - k >= 0):
                    spots.add((x, y))
    return spots


def reach(n, jump_px, dx_tiles=6):
    W, H, col = load(n)
    spots = standable(W, H, col)
    by_col = {}
    for x, y in spots:
        by_col.setdefault(x, []).append(y)
    start = min((s for s in spots if s[0] >= 4 and s[0] <= 6), key=lambda s: -s[1])
    seen = {start}
    todo = [start]
    while todo:
        x, y = todo.pop()
        for nx in range(max(0, x - dx_tiles - 8), min(W, x + dx_tiles + 9)):
            for ny in by_col.get(nx, []):
                rise = (y - ny) * 8
                if (nx, ny) in seen:
                    continue
                if rise > jump_px:
                    continue
                # a running jump carries further when it does not need the full height
                reach_x = dx_tiles + 2 if rise <= jump_px - 12 else dx_tiles - 1
                if rise <= 0:
                    reach_x += (-rise) // 16
                if abs(nx - x) > reach_x:
                    continue
                # a solid wall taller than the jump in between blocks the way
                lo, hi = sorted((x, nx))
                blocked = False
                for cx in range(lo + 1, hi):
                    top = min((yy for yy in range(H) if col[yy][cx] == T_SOLID), default=H)
                    if (min(y, ny) - top) * 8 > jump_px and top < min(y, ny):
                        blocked = True
                        break
                if blocked:
                    continue
                seen.add((nx, ny))
                todo.append((nx, ny))
    far = max(x for x, y in seen)
    return far, W


if __name__ == "__main__":
    jump = int(sys.argv[1]) if len(sys.argv) > 1 else 36
    bad = 0
    for n in range(1, 7):
        far, W = reach(n, jump)
        ok = far >= W - 4
        bad += not ok
        print(f"st{n}: reached x={far * 8} of {W * 8} {'ok' if ok else 'STUCK'}")
    sys.exit(1 if bad else 0)
