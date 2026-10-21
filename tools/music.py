"""Composes COMRADES' music and sound effects as Impulse Tracker modules
for SNESMOD (converted to a soundbank by smconv).

  build/sfx.it     sound effect samples (must be the first module)
  build/title.it   title theme, a gentle take on the stage tune
  build/stage1.it  "FFA Hoedown", the stage 1 theme (G major, 150 BPM)
  build/clear.it   stage clear fanfare (plays once)

Instruments are synthesised here: a soft saw "fiddle" lead, pulse chords,
a round bass, and kick/snare/hat drums.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from itwriter import Sample, Instrument, Cell, write_it, note, NOTE_CUT, NOTE_OFF

ROOT = os.path.join(os.path.dirname(__file__), "..")
BUILD = os.path.join(ROOT, "build")
SR = 16000
CYCLE = 64                     # samples per waveform cycle for melodic loops
C5 = 261.6256


def lowpass(x, a):
    y = np.zeros_like(x)
    acc = 0.0
    for _ in range(3):         # run several times so the loop wraps smoothly
        for i in range(len(x)):
            acc += a * (x[i] - acc)
            y[i] = acc
    return y


def wave(kind):
    t = np.arange(CYCLE) / CYCLE
    if kind == "saw":
        w = lowpass(2 * t - 1, 0.35)
    elif kind == "pulse25":
        w = lowpass(np.where(t < 0.25, 1.0, -0.6), 0.45)
    elif kind == "square":
        w = lowpass(np.where(t < 0.5, 1.0, -1.0), 0.4)
    elif kind == "bass":
        tri = 1 - 4 * np.abs(t - 0.5)
        w = lowpass(0.7 * tri + 0.3 * np.where(t < 0.5, 1.0, -1.0), 0.5)
    w = w - w.mean()
    w = w / np.abs(w).max()
    return w * 20000


def looped(name, kind, vol=64):
    w = wave(kind)
    data = np.tile(w, 2)
    return Sample(name, data, int(C5 * CYCLE), loop=(CYCLE, 2 * CYCLE), volume=vol)


def kick():
    n = int(SR * 0.16)
    t = np.arange(n) / SR
    f = 50 + 120 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 16) * 30000


def snare():
    n = int(SR * 0.16)
    t = np.arange(n) / SR
    rng = np.random.default_rng(3)
    noise = lowpass(rng.uniform(-1, 1, n), 0.6)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    return (noise * np.exp(-t * 18) * 0.8 + tone * 0.5) * 26000


def hat():
    n = int(SR * 0.05)
    t = np.arange(n) / SR
    rng = np.random.default_rng(7)
    x = rng.uniform(-1, 1, n)
    x = x - lowpass(x, 0.5)
    return x * np.exp(-t * 70) * 26000


def one_shot(name, data, vol=64):
    pad = (-len(data)) % 16
    data = np.concatenate([data, np.zeros(pad)])
    return Sample(name, data, SR, loop=None, volume=vol)


# ------------------------------------------------------------------ instruments
LEAD, BASS, CHORD, ARP, KICK, SNARE, HAT = range(7)


def song_kit():
    samples = [looped("fiddle", "saw"), looped("bass", "bass"), looped("chord", "pulse25", 48),
               looped("arp", "square", 48), one_shot("kick", kick()), one_shot("snare", snare()),
               one_shot("hat", hat(), 40)]
    instruments = [
        Instrument("fiddle", LEAD, envelope=[(0, 40), (3, 64), (14, 50), (80, 42)]),
        Instrument("bass", BASS, envelope=[(0, 64), (10, 52), (40, 30), (90, 0)]),
        Instrument("chord", CHORD, envelope=[(0, 56), (6, 30), (16, 0)]),
        Instrument("arp", ARP, envelope=[(0, 50), (8, 24), (30, 0)]),
        Instrument("kick", KICK),
        Instrument("snare", SNARE),
        Instrument("hat", HAT),
    ]
    return samples, instruments


# ------------------------------------------------------------------ the tune
# chords per bar (two chords = half a bar each)
PROGRESSION = ["G", "C", "D", "G", "G", "C", "Em D", "G",
               "C", "G", "Am", "D", "G", "Em", "C D", "G"]
CHORDS = {"G": ("G2", "B3", "D4"), "C": ("C3", "E4", "G4"), "D": ("D3", "F#4", "A4"),
          "Em": ("E2", "G4", "B4"), "Am": ("A2", "C4", "E4")}
FIFTH = {"G": "D3", "C": "G2", "D": "A2", "Em": "B2", "Am": "E3"}

MELODY = [
    [("B4", 2), ("D5", 2), ("G5", 4), ("F#5", 2), ("E5", 2), ("D5", 4)],
    [("E5", 2), ("G5", 2), ("E5", 2), ("C5", 2), ("D5", 4), ("E5", 4)],
    [("F#5", 2), ("A5", 2), ("F#5", 2), ("D5", 2), ("E5", 2), ("F#5", 2), ("A5", 4)],
    [("G5", 6), ("D5", 2), ("B4", 4), ("r", 4)],
    [("B4", 2), ("D5", 2), ("G5", 2), ("A5", 2), ("B5", 4), ("A5", 2), ("G5", 2)],
    [("E5", 2), ("G5", 2), ("C6", 4), ("B5", 2), ("A5", 2), ("G5", 4)],
    [("G5", 2), ("E5", 2), ("B4", 4), ("A4", 2), ("D5", 2), ("F#5", 4)],
    [("G5", 8), ("r", 4), ("D5", 2), ("D5", 2)],
    [("E5", 4), ("E5", 2), ("F#5", 2), ("G5", 4), ("E5", 4)],
    [("D5", 4), ("B4", 2), ("D5", 2), ("G5", 8)],
    [("C5", 2), ("E5", 2), ("A5", 4), ("G5", 2), ("F#5", 2), ("E5", 4)],
    [("F#5", 4), ("D5", 4), ("A4", 4), ("F#5", 2), ("A5", 2)],
    [("B5", 4), ("A5", 2), ("G5", 2), ("D5", 4), ("B4", 4)],
    [("E5", 2), ("G5", 2), ("B5", 4), ("A5", 2), ("G5", 2), ("E5", 4)],
    [("E5", 2), ("G5", 2), ("C6", 4), ("D6", 2), ("C6", 2), ("A5", 4)],
    [("G5", 12), ("r", 4)],
]


class Track:
    """Collects cells on an absolute row timeline for one channel."""

    def __init__(self):
        self.cells = {}

    def put(self, row, cell):
        self.cells[row] = cell


def melody_track(bars, ins, vol=None, transpose=0, vibrato=True):
    tr = Track()
    row = 0
    for bar in bars:
        for name, length in bar:
            if name == "r":
                tr.put(row, Cell(note=NOTE_OFF))
            else:
                tr.put(row, Cell(note=note(name) + transpose, ins=ins, vol=vol))
                if vibrato and length >= 4:
                    for k in range(2, length):
                        tr.put(row + k, Cell(cmd=8, arg=0x53))      # Hxy vibrato
            row += length
    return tr


def chord_list(bar_index):
    return PROGRESSION[bar_index % 16].split()


def bass_track(nbars):
    tr = Track()
    for b in range(nbars):
        chords = chord_list(b)
        base = b * 16
        if len(chords) == 1:
            c = chords[0]
            tr.put(base, Cell(note=note(CHORDS[c][0]), ins=BASS))
            tr.put(base + 6, Cell(note=note(CHORDS[c][0]), ins=BASS, vol=40))
            tr.put(base + 8, Cell(note=note(FIFTH[c]), ins=BASS))
            tr.put(base + 14, Cell(note=note(FIFTH[c]) + 2, ins=BASS, vol=44))
        else:
            for k, c in enumerate(chords):
                tr.put(base + k * 8, Cell(note=note(CHORDS[c][0]), ins=BASS))
                tr.put(base + k * 8 + 4, Cell(note=note(FIFTH[c]), ins=BASS))
    return tr


def chuck_tracks(nbars):
    """Off-beat chord stabs on beats 2 and 4 (and the 'and' of 4)."""
    t3, t5 = Track(), Track()
    for b in range(nbars):
        chords = chord_list(b)
        for k, row in enumerate((4, 12, 14)):
            c = chords[0] if (len(chords) == 1 or row < 8) else chords[1]
            v = 48 if row != 14 else 34
            t3.put(b * 16 + row, Cell(note=note(CHORDS[c][1]), ins=CHORD, vol=v))
            t5.put(b * 16 + row, Cell(note=note(CHORDS[c][2]), ins=CHORD, vol=v))
    return t3, t5


def drum_tracks(nbars):
    ks, hh = Track(), Track()
    for b in range(nbars):
        base = b * 16
        ks.put(base, Cell(note=note("C5"), ins=KICK, vol=64))
        ks.put(base + 8, Cell(note=note("C5"), ins=KICK, vol=64))
        ks.put(base + 4, Cell(note=note("C5"), ins=SNARE, vol=52))
        ks.put(base + 12, Cell(note=note("C5"), ins=SNARE, vol=52))
        if b % 4 == 3:                          # little fill every 4 bars
            ks.put(base + 10, Cell(note=note("C5"), ins=KICK, vol=56))
            ks.put(base + 14, Cell(note=note("C5"), ins=SNARE, vol=40))
            ks.put(base + 15, Cell(note=note("C5"), ins=SNARE, vol=46))
        for r in range(2, 16, 4):
            hh.put(base + r, Cell(note=note("C5"), ins=HAT, vol=30))
        for r in range(0, 16, 4):
            hh.put(base + r, Cell(note=note("C5"), ins=HAT, vol=14))
    return ks, hh


def arp_track(nbars):
    tr = Track()
    for b in range(nbars):
        chords = chord_list(b)
        for r in range(16):
            c = chords[0] if (len(chords) == 1 or r < 8) else chords[1]
            tones = [note(CHORDS[c][0]) + 12, note(CHORDS[c][1]), note(CHORDS[c][2]), note(CHORDS[c][1]) + 12]
            if r % 2 == 0:
                tr.put(b * 16 + r, Cell(note=tones[(r // 2) % 4], ins=ARP, vol=36 if r % 4 else 44))
    return tr


def to_patterns(tracks, nrows, per=64):
    pats = []
    for p in range(nrows // per):
        rows = []
        for r in range(per):
            rows.append([tr.cells.get(p * per + r) for tr in tracks])
        pats.append(rows)
    return pats


PANS = [32, 28, 16, 48, 32, 40, 24, 32]


def stage_theme():
    samples, instruments = song_kit()
    nbars = 16
    lead = melody_track(MELODY, LEAD)
    t3, t5 = chuck_tracks(nbars)
    ks, hh = drum_tracks(nbars)
    pats = to_patterns([lead, bass_track(nbars), t3, t5, ks, hh], nbars * 16)
    # intro pattern: drums + chords only, then the tune loops
    write_it(os.path.join(BUILD, "stage1.it"), "FFA Hoedown", samples, instruments, pats,
             [0, 1, 2, 3], speed=6, tempo=150, nchan=6, pans=PANS)


def title_theme():
    samples, instruments = song_kit()
    nbars = 16
    lead = melody_track(MELODY[8:] + MELODY[8:], LEAD, vol=44, transpose=-12)
    bass = Track()
    for b in range(nbars):
        for k, c in enumerate(chord_list(b)):
            bass.put(b * 16 + k * 8, Cell(note=note(CHORDS[c][0]), ins=BASS, vol=48))
    pats = to_patterns([lead, bass, arp_track(nbars)], nbars * 16)
    # first half of the loop without the melody, so the title opens softly
    write_it(os.path.join(BUILD, "title.it"), "Comrades", samples, instruments, pats,
             [0, 1, 2, 3], speed=6, tempo=110, nchan=3, pans=[32, 32, 32])


def clear_fanfare():
    samples, instruments = song_kit()
    fan = [("G5", 2), ("G5", 2), ("G5", 2), ("D5", 2), ("G5", 4), ("B5", 4),
           ("A5", 2), ("B5", 2), ("C6", 2), ("A5", 2), ("D6", 8), ("r", 8)]
    lead = melody_track([fan], LEAD, vibrato=True)
    bass = Track()
    for r, n in ((0, "G2"), (8, "G2"), (16, "D3"), (24, "G2")):
        bass.put(r, Cell(note=note(n), ins=BASS))
    t3, t5 = Track(), Track()
    for r, c in ((0, "G"), (8, "G"), (16, "D"), (24, "G")):
        t3.put(r, Cell(note=note(CHORDS[c][1]), ins=CHORD))
        t5.put(r, Cell(note=note(CHORDS[c][2]), ins=CHORD))
    ks = Track()
    for r in (0, 4, 8, 12, 16, 20, 22, 24):
        ks.put(r, Cell(note=note("C5"), ins=KICK if r % 8 == 0 else SNARE))
    rows = []
    for r in range(64):
        rows.append([tr.cells.get(r) for tr in (lead, bass, t3, t5, ks)])
    silent = [[None] * 5 for _ in range(64)]
    silent[0] = [Cell(note=NOTE_CUT)] * 5
    silent[63][0] = Cell(cmd=2, arg=1)          # Bxx: loop on the silent pattern
    write_it(os.path.join(BUILD, "clear.it"), "Stage Clear", samples, instruments, [rows, silent],
             [0, 1], speed=6, tempo=150, nchan=5)


# ------------------------------------------------------------------ sound effects
def sweep(f0, f1, dur, shape="square", decay=6.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    ph = np.cumsum(f) / SR
    if shape == "square":
        w = np.where((ph % 1) < 0.5, 1.0, -1.0)
    elif shape == "tri":
        w = 1 - 4 * np.abs((ph % 1) - 0.5)
    else:
        w = np.sin(2 * np.pi * ph)
    return w * np.exp(-t * decay)


def noise(dur, decay, a=0.5, seed=1):
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = lowpass(np.random.default_rng(seed).uniform(-1, 1, n), a)
    return x * np.exp(-t * decay)


SFX = ["jump", "throw", "splat", "stomp", "hurt", "bleat", "land"]


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def sfx_samples():
    out = {}
    out["jump"] = lowpass(sweep(260, 720, 0.13, "square", 4), 0.5) * 16000
    out["throw"] = mix(noise(0.11, 22, 0.35, 2) * 0.8, sweep(900, 400, 0.11, "tri", 20) * 0.4) * 22000
    out["splat"] = mix(noise(0.14, 26, 0.25, 3), sweep(300, 90, 0.14, "sine", 18) * 0.7) * 22000
    out["stomp"] = mix(sweep(220, 55, 0.16, "sine", 12), noise(0.08, 40, 0.3, 4) * 0.5) * 26000
    out["hurt"] = lowpass(sweep(700, 140, 0.28, "square", 5), 0.45) * 15000
    # goat bleat: buzzy tone with a wobble
    n = int(SR * 0.32)
    t = np.arange(n) / SR
    f = 330 + 40 * np.sin(2 * np.pi * 14 * t)
    ph = np.cumsum(f) / SR
    w = lowpass(2 * (ph % 1) - 1, 0.3) * np.minimum(1, t * 30) * np.exp(-t * 6)
    out["bleat"] = w * 22000
    out["land"] = noise(0.06, 50, 0.15, 5) * 18000
    return [one_shot(k, out[k]) for k in SFX]


def sfx_module():
    samples = sfx_samples()
    instruments = [Instrument(s.name, i) for i, s in enumerate(samples)]
    write_it(os.path.join(BUILD, "sfx.it"), "SFX", samples, instruments, [[[None] for _ in range(64)]],
             [0], nchan=1)
    with open(os.path.join(BUILD, "sfx.h"), "w") as f:
        f.write("// generated by tools/music.py\n")
        for i, k in enumerate(SFX):
            f.write(f"#define SFX_{k.upper()} {i}\n")
        f.write(f"#define SFX_COUNT {len(SFX)}\n")




if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True)
    sfx_module()
    title_theme()
    stage_theme()
    clear_fanfare()
    print("music written")
