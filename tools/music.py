"""Composes COMRADES' music and sound effects as Impulse Tracker modules
for SNESMOD (converted to a soundbank by smconv). Module order matters: the
effects module comes first and the game plays stage N as MOD_STAGE1 + N.

  sfx.it      sound effect samples
  title.it    "Comrades", the title theme
  stage1.it   "FFA Hoedown"           fiddle hoedown, G major, 168 BPM
  stage2.it   "Jam Sessions"          pop punk, E major, 156 BPM
  stage3.it   "Last Call"             punk rock, A major, 196 BPM
  stage4.it   "Lakefront"             festival house groove, D minor, 140 BPM
  stage5.it   "Order in the Court"    galloping castle rock, A minor, 144 BPM
  stage6.it   "Shuffleboard Shuffle"  hot swing, C major, 150 BPM
  boss.it     "Showdown"              driving minor rock, 180 BPM
  clear.it    stage clear fanfare (plays once)
  race.it     "Coast Highway"         fast rock, D major, 184 BPM
  range.it    "High Noon"             spaghetti western, A minor, 156 BPM
  ending.it   "Comrades for Life"     slow reprise of the title

Each song runs 32 bars (verse, chorus, verse, chorus, with the arpeggio
voice joining in) before it loops.

Instruments are synthesised here: leads (saw fiddle, square, soft pulse,
whistle, overdriven guitar), a round bass, chord and arpeggio voices, and
kick/snare/hat drums.
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
    elif kind == "pulse12":
        w = lowpass(np.where(t < 0.125, 1.0, -0.3), 0.5)
    elif kind == "square":
        w = lowpass(np.where(t < 0.5, 1.0, -1.0), 0.4)
    elif kind == "bass":
        tri = 1 - 4 * np.abs(t - 0.5)
        w = lowpass(0.7 * tri + 0.3 * np.where(t < 0.5, 1.0, -1.0), 0.5)
    elif kind == "whistle":
        w = np.sin(2 * np.pi * t) + 0.08 * np.sin(4 * np.pi * t)
    elif kind == "organ":
        w = np.sin(2 * np.pi * t) + 0.5 * np.sin(4 * np.pi * t) + 0.25 * np.sin(8 * np.pi * t)
    elif kind == "dist":
        w = np.tanh(4 * (2 * t - 1 + 0.6 * np.sin(4 * np.pi * t)))
        w = lowpass(w, 0.55)
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

LEAD_ENV = {
    "saw": [(0, 40), (3, 64), (14, 50), (80, 42)],
    "square": [(0, 48), (2, 60), (12, 44), (60, 36)],
    "pulse25": [(0, 50), (2, 60), (16, 40), (60, 30)],
    "pulse12": [(0, 50), (2, 58), (16, 40), (60, 30)],
    "whistle": [(0, 30), (5, 60), (30, 52), (90, 44)],
    "organ": [(0, 56), (4, 52), (100, 48)],
    "dist": [(0, 64), (10, 52), (60, 40)],
}


def song_kit(lead="saw", chord="pulse25", arp="square", chord_env=None, chord_vol=48):
    samples = [looped("lead", lead), looped("bass", "bass"), looped("chord", chord, chord_vol),
               looped("arp", arp, 48), one_shot("kick", kick()), one_shot("snare", snare()),
               one_shot("hat", hat(), 40)]
    instruments = [
        Instrument("lead", LEAD, envelope=LEAD_ENV[lead]),
        Instrument("bass", BASS, envelope=[(0, 64), (10, 52), (40, 30), (90, 0)]),
        Instrument("chord", CHORD, envelope=chord_env or [(0, 56), (6, 30), (16, 0)]),
        Instrument("arp", ARP, envelope=[(0, 50), (8, 24), (30, 0)]),
        Instrument("kick", KICK),
        Instrument("snare", SNARE),
        Instrument("hat", HAT),
    ]
    return samples, instruments


# ------------------------------------------------------------------ harmony helpers
NOTE_BASE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
             "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def chord_notes(name):
    """'Em' -> (bass note, [chord tones]) as IT note numbers. Supports
    major, m, 7, m7, maj7, dim, sus4 and 5 (power chord)."""
    root = name[:2] if len(name) > 1 and name[1] in "#b" else name[:1]
    q = name[len(root):]
    r = NOTE_BASE[root]
    ivs = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10), "maj7": (0, 4, 7, 11),
           "dim": (0, 3, 6), "sus4": (0, 5, 7), "5": (0, 7, 12)}[q]
    bass = 36 + r if r >= 4 else 48 + r          # E2..D#3 range
    tones = [60 + r + i for i in ivs]             # around middle C
    while tones[0] > 64:
        tones = [t - 12 for t in tones]
    return bass, tones


class Track:
    """Collects cells on an absolute row timeline for one channel."""

    def __init__(self):
        self.cells = {}

    def put(self, row, cell):
        self.cells[row] = cell


def parse_bar(s):
    out = []
    for tok in s.split():
        n, d = tok.split(":")
        out.append((n, int(d)))
    assert sum(d for _, d in out) == 16, s
    return out


def melody_track(bars, ins, vol=None, transpose=0, vibrato=True, vib=0x53):
    tr = Track()
    row = 0
    for bar in bars:
        if isinstance(bar, str):
            bar = parse_bar(bar)
        for name, length in bar:
            if name == "r":
                tr.put(row, Cell(note=NOTE_OFF))
            elif name == "-":
                pass                                  # tie
            else:
                tr.put(row, Cell(note=note(name) + transpose, ins=ins, vol=vol))
                if vibrato and length >= 4:
                    for k in range(2, length):
                        tr.put(row + k, Cell(cmd=8, arg=vib))      # Hxy vibrato
            row += length
    return tr


def bar_chords(prog, b):
    return prog[b % len(prog)].split()


def chord_at(prog, b, r):
    cs = bar_chords(prog, b)
    return cs[0] if (len(cs) == 1 or r < 8) else cs[1]


def bass_track(prog, nbars, style="root5", vol=None):
    tr = Track()
    for b in range(nbars):
        base = b * 16
        for r in range(16):
            c = chord_at(prog, b, r)
            bn, tones = chord_notes(c)
            fifth = bn + 7
            third = bn + (tones[1] - tones[0])
            if style == "root5":
                if r in (0, 8):
                    tr.put(base + r, Cell(note=bn if r == 0 else fifth, ins=BASS, vol=vol))
                elif r in (6, 14):
                    tr.put(base + r, Cell(note=bn if r == 6 else fifth + 2, ins=BASS, vol=40))
            elif style == "eighths":
                if r % 2 == 0:
                    tr.put(base + r, Cell(note=bn + (12 if r in (6, 14) else 0), ins=BASS, vol=vol or 56))
            elif style == "walk":
                if r % 4 == 0:
                    tr.put(base + r, Cell(note=[bn, third, fifth, bn + 9][r // 4], ins=BASS, vol=vol))
            elif style == "synco":
                if r in (0, 3, 6, 10, 12, 14):
                    tr.put(base + r, Cell(note=bn + (12 if r in (6, 14) else 0), ins=BASS, vol=vol))
                if r in (2, 8):
                    tr.put(base + r, Cell(note=NOTE_CUT))
            elif style == "gallop":
                if r % 4 in (0, 2, 3):
                    tr.put(base + r, Cell(note=bn if r % 8 < 4 else fifth, ins=BASS, vol=vol or 52))
            elif style == "sixteenths":
                if r % 2 == 0 or r in (13, 15):
                    tr.put(base + r, Cell(note=bn + (7 if r in (12, 14) else 0), ins=BASS, vol=vol or 54))
            elif style == "whole":
                if r in (0, 8):
                    tr.put(base + r, Cell(note=bn, ins=BASS, vol=vol))
    return tr


def comp_tracks(prog, nbars, style="chuck"):
    """Two chord voices (third and fifth) in an accompaniment pattern."""
    t3, t5 = Track(), Track()
    rows = {"chuck": (4, 12, 14), "strum": (0, 6, 8, 12, 14), "power": tuple(range(0, 16, 2)),
            "stab": (2, 6, 10, 11), "organ": (0, 8), "march": (0, 4, 8, 12), "swing": (4, 12),
            "offbeat": (2, 6, 10, 14)}[style]
    for b in range(nbars):
        for r in rows:
            c = chord_at(prog, b, r)
            bn, tones = chord_notes(c)
            v = 48 if style != "organ" else 40
            if style == "chuck" and r == 14:
                v = 34
            if style == "power":
                n3, n5 = tones[0] - 12 + 12, tones[0] + 7
                v = 44 if r % 4 == 0 else 36
            else:
                n3, n5 = tones[1], tones[2]
            t3.put(b * 16 + r, Cell(note=n3, ins=CHORD, vol=v))
            t5.put(b * 16 + r, Cell(note=n5, ins=CHORD, vol=v))
    return t3, t5


def arp_track(prog, nbars, step=2, vol=36, octave=12):
    tr = Track()
    for b in range(nbars):
        for r in range(0, 16, step):
            c = chord_at(prog, b, r)
            bn, tones = chord_notes(c)
            seq = [tones[0] + octave, tones[1] + octave, tones[2] + octave, tones[1] + octave + 12]
            tr.put(b * 16 + r, Cell(note=seq[(r // step) % 4], ins=ARP, vol=vol if r % 4 else vol + 8))
    return tr


def drum_tracks(nbars, style="rock", fill_every=4):
    ks, hh = Track(), Track()
    K = lambda r, v=64: ks.put(r, Cell(note=60, ins=KICK, vol=v))
    S = lambda r, v=52: ks.put(r, Cell(note=60, ins=SNARE, vol=v))
    H = lambda r, v=30: hh.put(r, Cell(note=60, ins=HAT, vol=v))
    for b in range(nbars):
        o = b * 16
        if style == "rock":
            K(o); K(o + 8); K(o + 10, 50); S(o + 4); S(o + 12)
            for r in range(0, 16, 2):
                H(o + r, 30 if r % 4 else 18)
        elif style == "hoedown":
            K(o); K(o + 8); S(o + 4); S(o + 12)
            for r in range(2, 16, 4):
                H(o + r, 30)
            for r in range(0, 16, 4):
                H(o + r, 14)
        elif style == "punk":
            for r in (0, 6, 8, 14):
                K(o + r, 64 if r in (0, 8) else 50)
            S(o + 4, 58); S(o + 12, 58)
            for r in range(0, 16, 2):
                H(o + r, 34)
        elif style == "four":
            for r in (0, 4, 8, 12):
                K(o + r)
            S(o + 4, 40); S(o + 12, 44)
            for r in (2, 6, 10, 14):
                H(o + r, 36)
            H(o + 15, 16)
        elif style == "march":
            K(o); K(o + 8)
            S(o + 4, 44); S(o + 12, 44)
            if b % 2 == 1:
                for r in (13, 14, 15):
                    S(o + r, 30 + (r - 13) * 6)
        elif style == "swing":
            K(o, 48); K(o + 8, 44)
            S(o + 4, 30); S(o + 12, 30)
            for r in (0, 3, 4, 7, 8, 11, 12, 15):
                H(o + r, 26 if r % 4 == 0 else 16)
        elif style == "gallop":
            K(o); K(o + 8)
            S(o + 4, 46); S(o + 12, 46)
            for r in range(16):
                if r % 4 in (0, 2, 3):
                    H(o + r, 24 if r % 4 == 0 else 16)
        elif style == "drive":
            for r in (0, 3, 6, 8, 11, 14):
                K(o + r, 60)
            S(o + 4, 56); S(o + 12, 56)
            for r in range(16):
                H(o + r, 26 if r % 2 == 0 else 12)
        elif style == "soft":
            K(o, 40); S(o + 8, 26)
            for r in range(0, 16, 4):
                H(o + r, 14)
        if fill_every and b % fill_every == fill_every - 1 and style not in ("soft", "swing", "march"):
            for r in (12, 13, 14, 15):
                ks.cells.pop(o + r, None)
            S(o + 12, 40); S(o + 13, 44); S(o + 14, 50); S(o + 15, 56)
    return ks, hh


def to_patterns(tracks, nrows, per=64):
    pats = []
    for p in range(nrows // per):
        rows = []
        for r in range(per):
            rows.append([tr.cells.get(p * per + r) for tr in tracks])
        pats.append(rows)
    return pats


PANS = [32, 28, 16, 48, 32, 40, 24, 32]


def song(path, title, kit, tempo, prog, melody, bass="root5", comp="chuck", drums="rock",
         arp=None, lead_vol=None, lead_transpose=0, second_half="octave", speed=6):
    """Builds a 16 bar song: the 8 (or 16) bar melody, and for 8 bar
    melodies a second pass with the lead up an octave over an arpeggio."""
    samples, instruments = kit
    melody = [parse_bar(b) if isinstance(b, str) else b for b in melody]
    if len(melody) == 8:
        if second_half == "octave":
            lead = melody_track(melody, LEAD, vol=lead_vol, transpose=lead_transpose)
            lead2 = melody_track(melody, LEAD, vol=lead_vol, transpose=lead_transpose + 12)
            for r, c in lead2.cells.items():
                lead.put(r + 128, c)
        else:
            lead = melody_track(melody + melody, LEAD, vol=lead_vol, transpose=lead_transpose)
    else:
        lead = melody_track(melody, LEAD, vol=lead_vol, transpose=lead_transpose)
    nbars = 16
    t3, t5 = comp_tracks(prog, nbars, comp)
    ks, hh = drum_tracks(nbars, drums)
    tracks = [lead, bass_track(prog, nbars, bass), t3, t5, ks, hh]
    if arp:
        a = arp_track(prog, nbars, **arp)
        if len(melody) == 8 and second_half == "octave":
            a.cells = {r: c for r, c in a.cells.items() if r >= 128}
        tracks.append(a)
    pats = to_patterns(tracks, nbars * 16)
    write_it(os.path.join(BUILD, path), title, samples, instruments, pats, list(range(len(pats))),
             speed=speed, tempo=tempo, nchan=len(tracks), pans=PANS[:len(tracks)])


def shift(tr, rows):
    out = Track()
    for r, c in tr.cells.items():
        out.put(r + rows, c)
    return out


def merge(dst, src):
    for r, c in src.cells.items():
        dst.put(r, c)


def song2(path, title, kit, tempo, sections, bass="root5", comp="chuck", drums="rock", arp=None,
          lead_vol=None, speed=6):
    """A song made of 8 bar sections, each with its own chord progression and
    melody: sections = [(prog, melody, transpose, with_arp), ...]. The whole
    song loops. Drum fills mark every fourth bar."""
    samples, instruments = kit
    lead, bs, t3, t5, ks, hh, ar = (Track() for _ in range(7))
    row = 0
    for prog, mel, tr, with_arp in sections:
        mel = [parse_bar(b) if isinstance(b, str) else b for b in mel]
        n = len(mel)
        merge(lead, shift(melody_track(mel, LEAD, vol=lead_vol, transpose=tr), row))
        merge(bs, shift(bass_track(prog, n, bass), row))
        a3, a5 = comp_tracks(prog, n, comp)
        merge(t3, shift(a3, row))
        merge(t5, shift(a5, row))
        k, h = drum_tracks(n, drums)
        merge(ks, shift(k, row))
        merge(hh, shift(h, row))
        if arp and with_arp:
            merge(ar, shift(arp_track(prog, n, **arp), row))
        row += n * 16
    tracks = [lead, bs, t3, t5, ks, hh] + ([ar] if arp else [])
    pats = to_patterns(tracks, row)
    write_it(os.path.join(BUILD, path), title, samples, instruments, pats, list(range(len(pats))),
             speed=speed, tempo=tempo, nchan=len(tracks), pans=PANS[:len(tracks)])


# ------------------------------------------------------------------ stage 1: FFA Hoedown
FFA_PROG = ["G", "C", "D", "G", "G", "C", "Em D", "G", "C", "G", "Am", "D", "G", "Em", "C D", "G"]
FFA_MELODY = [
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
# the fiddle break: running eighths
FFA_BREAK_PROG = ["G", "G", "C", "C", "D", "D", "G", "D"]
FFA_BREAK = ["G5:2 F#5:2 G5:2 A5:2 B5:2 A5:2 G5:2 D5:2",
             "E5:2 D5:2 B4:2 D5:2 G5:4 B5:4",
             "C6:2 B5:2 A5:2 G5:2 E5:2 G5:2 C6:2 E6:2",
             "D6:4 B5:2 G5:2 E5:4 C5:4",
             "D5:2 F#5:2 A5:2 D6:2 C6:2 A5:2 F#5:2 A5:2",
             "G5:2 F#5:2 E5:2 F#5:2 A5:4 D5:4",
             "B4:2 D5:2 G5:2 B5:2 D6:2 B5:2 G5:2 B5:2",
             "A5:2 G5:2 F#5:2 E5:2 D5:4 D5:2 D5:2"]


def stage1():
    a, b = FFA_PROG[:8], FFA_PROG[8:]
    song2("stage1.it", "FFA Hoedown", song_kit("saw", arp="pulse12"), 168,
          [(a, FFA_MELODY[:8], 0, False), (b, FFA_MELODY[8:], 0, True),
           (FFA_BREAK_PROG, FFA_BREAK, 0, True), (a, FFA_MELODY[:8], 12, True)],
          bass="root5", comp="chuck", drums="hoedown", arp=dict(step=2, vol=26))


# ------------------------------------------------------------------ stage 2: Jam Sessions
def stage2():
    prog = ["E", "B", "C#m", "A", "E", "B", "A", "B"]
    mel = ["G#4:2 B4:2 E5:4 D#5:2 E5:2 F#5:4",
           "D#5:4 B4:4 r:2 B4:2 C#5:2 D#5:2",
           "E5:2 E5:2 C#5:4 E5:2 G#5:2 F#5:4",
           "E5:4 C#5:2 B4:2 A4:4 r:4",
           "G#4:2 B4:2 E5:4 F#5:2 G#5:2 A5:4",
           "F#5:4 D#5:4 B4:2 C#5:2 D#5:4",
           "C#5:2 E5:2 A5:4 G#5:2 F#5:2 E5:4",
           "F#5:8 D#5:4 B4:4"]
    chorus_prog = ["A", "B", "G#m", "C#m", "A", "B", "E", "E"]
    chorus = ["C#5:2 E5:2 A5:4 A5:2 G#5:2 F#5:2 E5:2",
              "F#5:4 D#5:2 F#5:2 B5:4 r:4",
              "G#5:2 B5:2 D#6:4 C#6:2 B5:2 G#5:4",
              "C#6:4 B5:2 G#5:2 E5:4 C#5:4",
              "C#5:2 E5:2 A5:4 B5:2 C#6:2 B5:4",
              "A5:2 F#5:2 D#5:4 F#5:2 A5:2 B5:4",
              "G#5:4 E5:2 G#5:2 B5:4 E6:4",
              "E6:8 r:4 B4:2 B4:2"]
    song2("stage2.it", "Jam Sessions", song_kit("square", "pulse25"), 156,
          [(prog, mel, 0, False), (chorus_prog, chorus, 0, True), (prog, mel, 0, True), (chorus_prog, chorus, 0, True)],
          bass="eighths", comp="strum", drums="rock", arp=dict(step=2, vol=28))


# ------------------------------------------------------------------ stage 3: Last Call (punk)
def stage3():
    prog = ["A5", "A5", "D5", "E5", "F#5", "D5", "E5", "E5"]
    mel = ["A4:4 C#5:4 E5:4 C#5:4",
           "B4:2 A4:2 B4:4 C#5:8",
           "D5:4 F#5:4 A5:4 F#5:4",
           "E5:2 E5:2 G#5:4 B5:4 r:4",
           "F#5:4 A5:4 F#5:2 E5:2 C#5:4",
           "D5:4 C#5:2 B4:2 A4:8",
           "B4:2 C#5:2 E5:4 G#5:2 B5:2 E5:4",
           "E5:8 r:4 E5:2 E5:2"]
    bprog = ["D5", "E5", "C#5", "F#5", "D5", "E5", "A5", "A5"]
    bmel = ["F#5:2 F#5:2 F#5:2 E5:2 D5:4 A4:4",
            "E5:2 E5:2 E5:2 F#5:2 G#5:4 B5:4",
            "C#6:4 B5:2 A5:2 G#5:4 E5:4",
            "F#5:4 A5:4 C#6:8",
            "D6:2 C#6:2 A5:2 F#5:2 D5:4 F#5:4",
            "E5:2 G#5:2 B5:2 E6:2 D6:2 C#6:2 B5:4",
            "A5:4 C#6:4 E6:4 C#6:4",
            "A5:8 r:4 A4:2 A4:2"]
    song2("stage3.it", "Last Call", song_kit("dist", "dist", chord_env=[(0, 50), (4, 40), (8, 0)], chord_vol=44),
          196, [(prog, mel, 0, False), (bprog, bmel, 0, False), (prog, mel, 12, False), (bprog, bmel, 0, False)],
          bass="eighths", comp="power", drums="punk")


# ------------------------------------------------------------------ stage 4: Lakefront (festival groove)
def stage4():
    prog = ["Dm7", "Dm7", "Gm7", "A7", "Dm7", "Bb", "Gm7", "A7"]
    mel = ["D5:3 F5:3 A5:2 r:2 G5:2 F5:2 D5:2",
           "r:4 C5:2 D5:2 F5:4 D5:4",
           "G5:3 Bb5:3 D6:2 r:2 C6:2 Bb5:2 G5:2",
           "A5:6 G5:2 E5:4 C#5:4",
           "D5:3 F5:3 A5:2 r:2 C6:2 A5:2 F5:2",
           "Bb5:4 A5:2 F5:2 D5:4 r:4",
           "G5:2 G5:2 Bb5:2 A5:2 G5:4 F5:4",
           "E5:4 C#5:4 A4:4 r:4"]
    bprog = ["Bb", "C", "Am7", "Dm7", "Bb", "C", "A7", "A7"]
    bmel = ["F5:2 F5:2 D5:2 F5:2 r:2 G5:2 A5:4",
            "G5:2 G5:2 E5:2 G5:2 r:2 A5:2 Bb5:4",
            "A5:3 G5:3 E5:2 C5:4 E5:4",
            "D5:2 F5:2 A5:2 D6:2 C6:4 A5:4",
            "Bb5:2 A5:2 F5:2 D5:2 r:2 F5:2 Bb5:4",
            "C6:2 Bb5:2 G5:2 E5:2 r:2 G5:2 C6:4",
            "C#6:4 A5:4 E5:4 G5:4",
            "A5:2 G5:2 F5:2 E5:2 C#5:4 A4:4"]
    song2("stage4.it", "Lakefront", song_kit("pulse12", "pulse25", "square"), 140,
          [(prog, mel, 0, True), (bprog, bmel, 0, True), (prog, mel, 12, True), (bprog, bmel, 0, True)],
          bass="synco", comp="stab", drums="four", arp=dict(step=1, vol=22))


# ------------------------------------------------------------------ stage 5: Order in the Court
def stage5():
    prog = ["Am", "Dm", "E", "Am", "F", "C", "Dm E", "Am"]
    mel = ["A4:4 C5:2 E5:2 A5:6 G#5:2",
           "A5:2 F5:2 D5:4 F5:4 A5:4",
           "G#5:4 B5:4 E5:4 D5:2 C5:2",
           "C5:2 B4:2 A4:4 E4:4 A4:4",
           "C5:4 F5:4 A5:4 G5:2 F5:2",
           "E5:4 G5:4 C6:4 B5:2 A5:2",
           "F5:2 E5:2 D5:4 B4:2 C5:2 D5:2 G#5:2",
           "A5:12 r:4"]
    bprog = ["F", "G", "Em", "Am", "Dm", "E", "F E", "Am"]
    bmel = ["A5:4 C6:4 F5:4 A5:4",
            "B5:4 D6:4 G5:4 B5:4",
            "G5:2 F5:2 E5:2 F5:2 G5:4 B5:4",
            "C6:2 B5:2 A5:2 G5:2 A5:8",
            "D5:2 F5:2 A5:2 D6:2 C6:2 A5:2 F5:4",
            "E5:2 G#5:2 B5:2 E6:2 D6:2 B5:2 G#5:4",
            "A5:2 G5:2 F5:4 E5:2 D5:2 C5:2 B4:2",
            "A4:8 r:4 E5:2 E5:2"]
    song2("stage5.it", "Order in the Court",
          song_kit("organ", "dist", "pulse12", chord_env=[(0, 50), (4, 38), (10, 0)], chord_vol=40),
          144, [(prog, mel, 0, False), (bprog, bmel, 0, True), (prog, mel, 0, True), (bprog, bmel, 0, True)],
          bass="gallop", comp="power", drums="gallop", arp=dict(step=2, vol=26))


# ------------------------------------------------------------------ stage 6: Shuffleboard Shuffle
def stage6():
    prog = ["C", "Am", "Dm", "G7", "C", "A7", "Dm G7", "C"]
    mel = ["E5:3 G5:1 E5:4 C5:4 r:4",
           "C5:3 E5:1 A5:4 G5:4 E5:4",
           "F5:3 A5:1 F5:4 D5:4 F5:4",
           "B4:3 D5:1 G5:8 r:4",
           "E5:3 G5:1 C6:4 B5:4 A5:4",
           "C#5:3 E5:1 A5:4 G5:4 E5:4",
           "F5:3 A5:1 D6:4 B5:3 G5:1 F5:4",
           "E5:8 C5:4 r:4"]
    bprog = ["F", "C", "D7", "G7", "C", "A7", "D7 G7", "C"]
    bmel = ["A5:3 C6:1 A5:4 F5:4 A5:4",
            "G5:3 E5:1 C5:4 E5:4 G5:4",
            "F#5:3 A5:1 D6:4 C6:4 A5:4",
            "B5:3 A5:1 G5:4 F5:4 D5:4",
            "E5:3 G5:1 C6:4 E6:4 C6:4",
            "C#6:3 A5:1 E5:4 G5:4 A5:4",
            "F5:2 A5:2 D6:2 C6:2 B5:2 A5:2 G5:2 F5:2",
            "E5:4 G5:4 C6:8"]
    song2("stage6.it", "Shuffleboard Shuffle",
          song_kit("whistle", "pulse25", chord_env=[(0, 44), (8, 30), (24, 0)]), 150,
          [(prog, mel, 0, False), (bprog, bmel, 0, True), (prog, mel, 0, True), (bprog, bmel, 0, True)],
          bass="walk", comp="swing", drums="swing", arp=dict(step=4, vol=24))


# ------------------------------------------------------------------ boss: Showdown
def boss():
    prog = ["Em", "C", "D", "B", "Em", "C", "Am", "B"]
    mel = ["E5:4 r:2 E5:2 G5:4 F#5:4",
           "E5:2 D5:2 E5:4 G5:2 A5:2 B5:4",
           "A5:4 F#5:4 D5:4 A5:4",
           "B5:8 D#5:4 F#5:4",
           "E5:4 r:2 E5:2 B5:4 A5:4",
           "G5:2 F#5:2 E5:4 G5:4 C6:4",
           "B5:4 A5:4 G5:2 F#5:2 E5:4",
           "D#5:8 F#5:4 B5:4"]
    bprog = ["C", "D", "Em", "Em", "C", "D", "B", "B"]
    bmel = ["C6:2 B5:2 G5:2 E5:2 C5:4 E5:4",
            "D6:2 C6:2 A5:2 F#5:2 D5:4 F#5:4",
            "E5:2 G5:2 B5:2 E6:2 D6:2 B5:2 G5:2 B5:2",
            "E6:8 B5:4 G5:4",
            "C6:2 B5:2 G5:2 E5:2 C5:2 E5:2 G5:2 C6:2",
            "D6:2 C6:2 A5:2 F#5:2 D5:2 F#5:2 A5:2 D6:2",
            "D#6:4 B5:4 F#5:4 A5:4",
            "B5:2 A5:2 G5:2 F#5:2 D#5:8"]
    song2("boss.it", "Showdown", song_kit("dist", "pulse25", "square"), 180,
          [(prog, mel, 0, False), (bprog, bmel, 0, True), (prog, mel, 0, True), (bprog, bmel, 0, True)],
          bass="sixteenths", comp="offbeat", drums="drive", arp=dict(step=1, vol=20))


# ------------------------------------------------------------------ race: Coast Highway
def race():
    prog = ["D", "C", "G", "D", "D", "C", "G", "A"]
    mel = ["F#5:2 A5:2 D6:4 C6:2 A5:2 F#5:4",
           "G5:4 E5:2 C5:2 E5:4 G5:4",
           "B5:4 G5:2 D5:2 G5:2 A5:2 B5:4",
           "A5:8 F#5:4 D5:4",
           "F#5:2 A5:2 D6:4 E6:2 D6:2 A5:4",
           "C6:4 G5:2 E5:2 G5:4 C6:4",
           "B5:2 A5:2 G5:4 D5:4 B5:4",
           "A5:8 C#6:4 E6:4"]
    bprog = ["G", "A", "Bm", "G", "G", "A", "D", "D"]
    bmel = ["B5:2 D6:2 B5:2 G5:2 D5:4 G5:4",
            "C#6:2 E6:2 C#6:2 A5:2 E5:4 A5:4",
            "D6:4 B5:2 F#5:2 D5:4 F#5:4",
            "G5:2 A5:2 B5:2 D6:2 E6:8",
            "D6:2 B5:2 G5:2 B5:2 D6:2 G6:2 D6:2 B5:2",
            "C#6:2 A5:2 E5:2 A5:2 C#6:2 E6:2 C#6:2 A5:2",
            "D6:4 F#5:4 A5:4 D6:4",
            "D6:8 r:4 A5:2 A5:2"]
    song2("race.it", "Coast Highway",
          song_kit("square", "dist", chord_env=[(0, 48), (4, 36), (8, 0)], chord_vol=40), 184,
          [(prog, mel, 0, False), (bprog, bmel, 0, True), (prog, mel, 0, True), (bprog, bmel, 0, True)],
          bass="eighths", comp="power", drums="drive", arp=dict(step=2, vol=24))


# ------------------------------------------------------------------ range: High Noon
def range_theme():
    prog = ["Am", "G", "F", "E", "Am", "G", "F", "E"]
    mel = ["A4:2 E5:2 A5:8 G5:2 E5:2",
           "D5:2 G5:2 B5:8 A5:2 G5:2",
           "F5:4 A5:4 C6:4 A5:4",
           "G#5:12 r:4",
           "A5:2 A5:2 C6:4 B5:2 A5:2 G5:4",
           "G5:2 D5:2 B4:4 D5:4 G5:4",
           "F5:2 E5:2 F5:2 A5:2 C6:4 B5:2 A5:2",
           "B5:8 G#5:4 E5:4"]
    bprog = ["F", "C", "G", "Am", "F", "C", "E", "E"]
    bmel = ["A5:2 C6:2 F6:4 E6:2 C6:2 A5:4",
            "G5:2 C6:2 E6:4 D6:2 C6:2 G5:4",
            "B5:4 D6:4 G5:4 B5:4",
            "A5:2 B5:2 C6:2 E6:2 A5:8",
            "F5:2 A5:2 C6:2 F6:2 E6:2 C6:2 A5:4",
            "E5:2 G5:2 C6:2 E6:2 D6:2 C6:2 G5:4",
            "G#5:4 B5:4 E6:4 D6:4",
            "E6:8 B5:4 G#5:4"]
    song2("range.it", "High Noon", song_kit("whistle", "pulse12", chord_env=[(0, 50), (6, 30), (14, 0)]), 156,
          [(prog, mel, 0, False), (bprog, bmel, 0, True), (prog, mel, 0, True), (bprog, bmel, 0, True)],
          bass="gallop", comp="offbeat", drums="gallop", arp=dict(step=2, vol=22))


# ------------------------------------------------------------------ title and ending
def title_theme():
    a, b = FFA_PROG[:8], FFA_PROG[8:]
    song2("title.it", "Comrades", song_kit("saw", "pulse25", "pulse12"), 140,
          [(a, FFA_MELODY[:8], 0, True), (b, FFA_MELODY[8:], 0, True)],
          bass="eighths", comp="strum", drums="rock", arp=dict(step=2, vol=24))


def ending_theme():
    samples, instruments = song_kit("whistle", "pulse25", chord_env=[(0, 40), (16, 28), (60, 0)])
    nbars = 16
    lead = melody_track(FFA_MELODY, LEAD, vol=44, transpose=-12, vib=0x42)
    bass = bass_track(FFA_PROG, nbars, "whole", vol=44)
    t3, t5 = comp_tracks(FFA_PROG, nbars, "organ")
    ks, hh = drum_tracks(nbars, "soft")
    pats = to_patterns([lead, bass, t3, t5, ks, hh, arp_track(FFA_PROG, nbars, step=4, vol=24)], nbars * 16)
    write_it(os.path.join(BUILD, "ending.it"), "Comrades for Life", samples, instruments, pats,
             [0, 1, 2, 3], speed=6, tempo=96, nchan=7, pans=PANS[:7])


def clear_fanfare():
    samples, instruments = song_kit("saw")
    fan = [("G5", 2), ("G5", 2), ("G5", 2), ("D5", 2), ("G5", 4), ("B5", 4),
           ("A5", 2), ("B5", 2), ("C6", 2), ("A5", 2), ("D6", 8), ("r", 8)]
    lead = melody_track([fan], LEAD, vibrato=True)
    bass = Track()
    for r, n in ((0, "G2"), (8, "G2"), (16, "D3"), (24, "G2")):
        bass.put(r, Cell(note=note(n), ins=BASS))
    t3, t5 = Track(), Track()
    for r, c in ((0, "G"), (8, "G"), (16, "D"), (24, "G")):
        tones = chord_notes(c)[1]
        t3.put(r, Cell(note=tones[1], ins=CHORD))
        t5.put(r, Cell(note=tones[2], ins=CHORD))
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


def tone(freqs, dur_each, shape="square", decay=10):
    return np.concatenate([sweep(f, f, dur_each, shape, decay) for f in freqs])


SFX = ["jump", "throw", "splat", "stomp", "hurt", "bleat", "land", "heart", "bang", "ding", "crash", "boost",
       "roar", "select", "powerup", "crack", "oneup"]


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
    # critter bleat: buzzy tone with a wobble
    n = int(SR * 0.26)
    t = np.arange(n) / SR
    f = 330 + 40 * np.sin(2 * np.pi * 14 * t)
    ph = np.cumsum(f) / SR
    w = lowpass(2 * (ph % 1) - 1, 0.3) * np.minimum(1, t * 30) * np.exp(-t * 7)
    out["bleat"] = w * 22000
    out["land"] = noise(0.06, 50, 0.15, 5) * 18000
    out["heart"] = lowpass(tone([660, 880, 1320], 0.06, "square", 8), 0.5) * 14000
    out["bang"] = mix(noise(0.22, 16, 0.7, 9), sweep(160, 50, 0.2, "sine", 14) * 0.8) * 28000
    out["ding"] = mix(sweep(1760, 1760, 0.35, "sine", 7), sweep(2640, 2640, 0.3, "sine", 12) * 0.4) * 20000
    out["crash"] = mix(noise(0.4, 7, 0.6, 11), sweep(200, 60, 0.3, "square", 8) * 0.3) * 24000
    out["boost"] = lowpass(sweep(200, 1400, 0.3, "square", 3), 0.4) * 13000
    n = int(SR * 0.5)
    t = np.arange(n) / SR
    f = 110 + 30 * np.sin(2 * np.pi * 9 * t)
    ph = np.cumsum(f) / SR
    roar = lowpass(np.tanh(3 * np.sin(2 * np.pi * ph)), 0.35) * np.minimum(1, t * 12) * np.exp(-t * 3)
    out["roar"] = mix(roar, noise(0.5, 4, 0.2, 13) * 0.5) * 24000
    out["select"] = lowpass(tone([990, 1320], 0.04, "square", 20), 0.5) * 12000
    out["powerup"] = lowpass(tone([523, 659, 784, 1047, 1319], 0.05, "square", 6), 0.5) * 14000
    # a wooden crack: a sharp noise burst with a knock under it
    out["crack"] = mix(noise(0.12, 30, 0.8, 21), sweep(420, 160, 0.1, "tri", 25) * 0.7,
                       noise(0.05, 60, 0.95, 22) * 0.6) * 24000
    out["oneup"] = lowpass(tone([659, 784, 1319, 1047, 1175, 1568], 0.07, "square", 5), 0.5) * 14000
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
    stage1()
    stage2()
    stage3()
    stage4()
    stage5()
    stage6()
    boss()
    clear_fanfare()
    race()
    range_theme()
    ending_theme()
    print("music written")
