"""Minimal Impulse Tracker (.it) writer, enough for SNESMOD/smconv.

Instrument mode, one sample per instrument, 16-bit signed mono samples,
optional volume envelope. Patterns are given as rows of per-channel cells.
"""
import struct

NOTE_NAMES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
NOTE_OFF, NOTE_CUT = 255, 254


def note(name):
    """'G5' -> IT note number (C-0 = 0, C-5 = 60)."""
    if name[1] == "#":
        return NOTE_NAMES[name[:2]] + 12 * int(name[2:])
    return NOTE_NAMES[name[0]] + 12 * int(name[1:])


class Sample:
    def __init__(self, name, data, c5speed, loop=None, volume=64):
        self.name, self.data, self.c5speed, self.loop, self.volume = name, data, c5speed, loop, volume


class Instrument:
    def __init__(self, name, sample_index, envelope=None, fadeout=0):
        """envelope: list of (tick, volume 0-64) nodes, or None."""
        self.name, self.sample_index, self.envelope, self.fadeout = name, sample_index, envelope, fadeout


class Cell:
    __slots__ = ("note", "ins", "vol", "cmd", "arg")

    def __init__(self, note=None, ins=None, vol=None, cmd=None, arg=0):
        self.note, self.ins, self.vol, self.cmd, self.arg = note, ins, vol, cmd, arg


def _pad(s, n):
    b = s.encode("ascii")[:n]
    return b + b"\0" * (n - len(b))


def _sample_header(s, data_ptr):
    flags = 1 | 2 | (16 if s.loop else 0)
    lb, le = s.loop if s.loop else (0, 0)
    h = b"IMPS" + _pad(s.name[:12], 12) + b"\0"
    h += struct.pack("<BBB", 64, flags, s.volume)
    h += _pad(s.name, 26)
    h += struct.pack("<BB", 1, 32)          # signed samples, default pan (unused)
    h += struct.pack("<IIIIIII", len(s.data), lb, le, s.c5speed, 0, 0, data_ptr)
    h += struct.pack("<BBBB", 0, 0, 0, 0)
    assert len(h) == 0x50
    return h


def _instrument(ins):
    h = b"IMPI" + _pad(ins.name[:12], 12) + b"\0"
    h += struct.pack("<BBBHBBBBBBHBB", 0, 0, 0, ins.fadeout, 0, 60, 128, 32 | 0x80, 0, 0, 0x0214, 1, 0)
    h += _pad(ins.name, 26)
    h += struct.pack("<BBBBH", 0, 0, 0, 0, 0)
    assert len(h) == 0x40
    for n in range(120):
        h += struct.pack("<BB", n, ins.sample_index + 1)
    env = ins.envelope
    if env:
        h += struct.pack("<BBBBBB", 1, len(env), 0, 0, 0, 0)
        nodes = list(env) + [(0, 0)] * (25 - len(env))
        for tick, vol in nodes:
            h += struct.pack("<BH", vol, tick)
        h += b"\0"
    else:
        h += b"\0" * 82
    h += b"\0" * 82 * 2                     # panning and pitch envelopes disabled
    h += b"\0" * 4
    return h


def _pattern(rows, nchan):
    out = bytearray()
    for row in rows:
        for ch in range(nchan):
            c = row[ch] if ch < len(row) else None
            if c is None:
                continue
            mask = 0
            body = bytearray()
            if c.note is not None:
                mask |= 1
                body.append(c.note)
            if c.ins is not None:
                mask |= 2
                body.append(c.ins + 1)
            if c.vol is not None:
                mask |= 4
                body.append(c.vol)
            if c.cmd is not None:
                mask |= 8
                body += bytes([c.cmd, c.arg])
            if not mask:
                continue
            out.append((ch + 1) | 0x80)
            out.append(mask)
            out += body
        out.append(0)
    return struct.pack("<HH4x", len(out), len(rows)) + bytes(out)


def write_it(path, title, samples, instruments, patterns, orders, speed=6, tempo=125, nchan=8, pans=None):
    hdr = b"IMPM" + _pad(title, 26) + struct.pack("<H", 0x1004)
    ordlist = list(orders) + [255]
    hdr += struct.pack("<HHHHHHHH", len(ordlist), len(instruments), len(samples), len(patterns),
                       0x0214, 0x0214, 0x0D, 0)
    hdr += struct.pack("<BBBBBBHII", 128, 48, speed, tempo, 128, 0, 0, 0, 0)
    chpan = []
    for ch in range(64):
        p = 32 if pans is None or ch >= len(pans) else pans[ch]
        chpan.append(p if ch < nchan else 32 | 128)
    hdr += bytes(chpan) + bytes([64] * 64)
    assert len(hdr) == 0xC0

    base = 0xC0 + len(ordlist) + 4 * (len(instruments) + len(samples) + len(patterns))
    blobs = []
    offs_ins, offs_smp, offs_pat = [], [], []
    pos = base
    for ins in instruments:
        b = _instrument(ins)
        offs_ins.append(pos)
        blobs.append(b)
        pos += len(b)
    smp_hdr_pos = []
    for s in samples:
        offs_smp.append(pos)
        smp_hdr_pos.append(pos)
        blobs.append(None)                  # placeholder, filled once data offsets are known
        pos += 0x50
    pat_blobs = []
    for p in patterns:
        b = _pattern(p, nchan)
        offs_pat.append(pos)
        pat_blobs.append(b)
        pos += len(b)
    data_ptrs = []
    for s in samples:
        data_ptrs.append(pos)
        pos += 2 * len(s.data)

    out = bytearray(hdr)
    out += bytes(ordlist)
    for o in offs_ins + offs_smp + offs_pat:
        out += struct.pack("<I", o)
    for b in blobs:
        if b is not None:
            out += b
    for s, dp in zip(samples, data_ptrs):
        out += _sample_header(s, dp)
    for b in pat_blobs:
        out += b
    for s in samples:
        out += struct.pack("<%dh" % len(s.data), *[max(-32768, min(32767, int(v))) for v in s.data])
    with open(path, "wb") as f:
        f.write(out)
