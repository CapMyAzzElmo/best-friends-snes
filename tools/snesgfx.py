"""Writers for SNES graphics data and the PVSnesLib map engine formats."""
import struct


def tile_4bpp(px):
    """px: 8 rows of 8 colour indices (0-15) -> 32 bytes of SNES 4bpp planar data."""
    out = bytearray(32)
    for y in range(8):
        for x in range(8):
            v = px[y][x]
            bit = 7 - x
            out[y * 2] |= (v & 1) << bit
            out[y * 2 + 1] |= ((v >> 1) & 1) << bit
            out[16 + y * 2] |= ((v >> 2) & 1) << bit
            out[16 + y * 2 + 1] |= ((v >> 3) & 1) << bit
    return bytes(out)


def color15(rgb):
    r, g, b = (v >> 3 for v in rgb)
    return struct.pack("<H", r | (g << 5) | (b << 10))


def palette_bytes(colors):
    return b"".join(color15(c) for c in colors)


def words(values):
    return b"".join(struct.pack("<H", v & 0xFFFF) for v in values)
