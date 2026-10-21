"""Generates every stage's enemies, projectiles and boss.

Per stage N it writes (indexed PNG previews in art/sprites/, VRAM data in build/):
  stN_foes   32x32 frames: foe A walk0-3, charge0-1, hurt (0-6),
                           foe B walk0-3, charge0-1, hurt (7-13)
  stN_small  16x16 frames: hero shot 0-1, spark 2-4, heart 5,
                           foe C walk0-1, alt0-1, hurt (6-10), boss shot 11-12
  stN_boss   64x64 frames: idle0, idle1, attack, hurt (stored as 2x2 32x32
             quadrants: frame f quadrant q -> 32x32 frame f*4+q)
Palettes: stN_spra.pal (sprite palette 2: foe A, foe C, hero shots, sparks,
hearts), stN_sprb.pal (palette 5: foe B), stN_boss.pal (palette 6).

Sprite palette 2 keeps a fixed layout so sparks and hearts work everywhere:
1 outline, 9 yellow, 14 white, 15 red; 10-13 colour the hero's shot.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, ascii_canvas, capsule, ellipse, shade, outlined, to_image, snes_color, rot
from snesgfx import palette_bytes
from sprites_build import grid_pic
import critters
import heroes

ROOT = os.path.join(os.path.dirname(__file__), "..")
SPR = os.path.join(ROOT, "art", "sprites")
BUILD = os.path.join(ROOT, "build")
MAGENTA = (255, 0, 255)
OUT = (20, 16, 28)
SKIN = [(252, 208, 168), (228, 164, 124), (180, 112, 88)]
YELLOW, WHITE, RED = (240, 196, 56), (248, 248, 240), (224, 56, 56)


def pal_a(c2_8, shot4):
    """Sprite palette 2: seven foe colours at 2-8, four shot colours at 10-13."""
    return [MAGENTA, OUT] + list(c2_8) + [YELLOW] + list(shot4) + [WHITE, RED]


def stack(frames, size):
    sheet = Canvas(size, size * len(frames))
    for k, f in enumerate(frames):
        sheet.blit(f, 0, size * k)
    return sheet


def flash(c, keep=(1,), to=14):
    """Hurt frame: everything but the outline flashes white."""
    out = c.copy()
    for y in range(c.h):
        for x in range(c.w):
            if out.px[y][x] and out.px[y][x] not in keep:
                out.px[y][x] = to
    return out


def compose(*layers, size=32):
    out = Canvas(size, size)
    for layer in layers:
        out.blit(outlined(layer, 1))
    return out


def feet_down(c):
    low = max((y for y in range(c.h) for x in range(c.w) if c.px[y][x]), default=c.h - 1)
    return c.shifted(0, c.h - 1 - low)


# ------------------------------------------------------------------ common bits
def spark(n):
    return critters.spark(n)


def heart():
    return ascii_canvas(critters.HEART + ["." * 16] * 4, {"o": 1, "R": 15, "W": 14})


def shot_round(r, light, mid, dark, hl=14, spin=0):
    c = Canvas(16, 16)
    ellipse(c, 8, 8, r, r, mid)
    shade(c, mid, light, dark)
    c.set(7 - spin, 7, hl)
    return outlined(c, 1)


# ------------------------------------------------------------------ humanoid foes
def humanoid(name, pal, head, head_legend, torso, torso_legend, spec):
    base = dict(head_top=1, head_x=10, torso_x=11, torso_y=11, hip_y=19, shoulder_y=13,
                thigh=5.5, shin=5.5, upper=4.2, fore=4.0, leg_r=1.8, arm_r=1.4,
                rip=None, hand_in_pocket=False)
    base.update(spec)
    return heroes.Hero(name, pal, head, head_legend, torso, torso_legend, base)


def humanoid_frames(h):
    walk = [heroes.frame(h, f"run{i}") for i in (0, 2, 4, 6)]
    charge = [heroes.frame(h, "run1"), heroes.frame(h, "run5")]
    hurt = flash(heroes.frame(h, "hurt"), keep=(1,))
    return walk + charge + [hurt]


# ================================================================== STAGE 1
def stage1():
    pa = critters.PAL
    pb = critters.PIG_PAL
    big = [critters.beast("goat", f) for f in ("walk0", "walk1", "walk2", "walk3", "charge0", "charge1", "hurt")]
    big += [critters.beast("pig", f) for f in ("walk0", "walk1", "walk2", "walk3", "charge0", "charge1", "hurt")]
    small = [critters.grape(0), critters.grape(1), spark(0), spark(1), spark(2), heart(),
             critters.chicken("walk0"), critters.chicken("walk1"), critters.chicken("flap0"),
             critters.chicken("flap1"), critters.chicken("hurt")]
    small += [mud_clod(0), mud_clod(1)]
    return pa, pb, BULL_PAL, big, small, [bull(f) for f in ("idle0", "idle1", "attack", "hurt")]


BULL_PAL = [MAGENTA, OUT,
            (150, 90, 60), (112, 64, 42), (76, 42, 30),            # 2-4 hide
            (196, 140, 100),                                       # 5 hide light
            (236, 228, 210), (190, 178, 160),                      # 6-7 horn
            (200, 200, 210),                                       # 8 nose ring
            (240, 196, 56),                                        # 9 eye
            (60, 40, 34),                                          # 10 hooves / dark
            (232, 150, 150),                                       # 11 nose
            (90, 60, 40), (130, 90, 60),                           # 12-13 mud
            (248, 248, 240), (224, 56, 56)]                        # 14 white, 15 red (ribbon)


def mud_clod(i):
    c = Canvas(16, 16)
    ellipse(c, 8, 8, 4, 3.4, 12)
    for (x, y) in ((6, 6), (9, 7), (7, 10)) if i == 0 else ((10, 6), (6, 8), (8, 10)):
        c.set(x, y, 13)
    return outlined(c, 1)


def bull(frame):
    attack = frame == "attack"
    bob = 1 if frame == "idle1" else 0
    c = Canvas(64, 64)
    legs = Canvas(64, 64)
    by = 36 + bob
    lean = 4 if attack else 0
    for (hx, sw) in ((14, -3 if attack else 0), (22, 3 if attack else 0), (40, -2), (48, 2 if attack else 0)):
        capsule(legs, (hx + lean // 2, by + 6), (hx + sw, 61), 3.2, 3)
        capsule(legs, (hx + sw - 2, 61), (hx + sw + 3, 61), 1.6, 10)
    shade(legs, 3, 2, 4)
    body = Canvas(64, 64)
    ellipse(body, 30 + lean, by, 22, 13, 2)
    ellipse(body, 40 + lean, by - 6, 12, 9, 2)              # shoulder hump
    shade(body, 2, 5, 3)
    capsule(body, (9 + lean, by - 6), (5, by + 6), 1.2, 4)   # tail
    ellipse(body, 5, by + 7, 2, 2.5, 10)
    head = Canvas(64, 64)
    hx, hy = (52 + lean, by - 2 + (8 if attack else 0))
    ellipse(head, hx, hy, 9, 8, 2)
    ellipse(head, hx + 6, hy + 4, 5, 4, 11)                  # muzzle
    shade(head, 2, 5, 3)
    head.set(int(hx + 8), int(hy + 4), 1); head.set(int(hx + 5), int(hy + 4), 1)
    ellipse(head, hx + 7, hy + 8, 2.4, 2.4, 8)               # nose ring
    ellipse(head, hx + 7, hy + 8, 1.2, 1.2, 0)
    head.set(int(hx + 2), int(hy - 3), 9 if not attack else 15)   # eye (red when charging)
    head.set(int(hx + 3), int(hy - 3), 1)
    horns = Canvas(64, 64)
    if attack:
        pts_a = [(hx + 2, hy - 6), (hx + 10, hy - 9), (hx + 15, hy - 6)]
        pts_b = [(hx - 4, hy - 6), (hx + 2, hy - 12), (hx + 9, hy - 13)]
    else:
        pts_a = [(hx - 2, hy - 6), (hx - 6, hy - 13), (hx - 2, hy - 18)]
        pts_b = [(hx + 4, hy - 6), (hx + 8, hy - 13), (hx + 5, hy - 18)]
    for pts in (pts_b, pts_a):
        for a, b in zip(pts, pts[1:]):
            capsule(horns, a, b, 1.8 if a == pts[0] else 1.2, 6)
    shade(horns, 6, None, 7)
    ribbon = Canvas(64, 64)
    ellipse(ribbon, 34 + lean, by - 2, 5, 5, 15)              # champion rosette
    ellipse(ribbon, 34 + lean, by - 2, 2, 2, 9)
    capsule(ribbon, (32 + lean, by + 2), (30 + lean, by + 9), 1, 15)
    capsule(ribbon, (36 + lean, by + 2), (38 + lean, by + 9), 1, 15)
    out = compose(legs, body, head, horns, ribbon, size=64)
    if attack:                                              # dust kicked up
        for (x, y) in ((2, 58), (5, 55), (1, 52), (8, 60)):
            ellipse(out, x, y, 2, 1.5, 7)
    out = feet_down(out)
    if frame == "hurt":
        out = flash(out, keep=(1, 15, 9))
    return out


# ================================================================== STAGE 2
def stage2():
    pa = pal_a([(240, 160, 70), (200, 110, 40), (140, 70, 30),     # 2-4 tabby orange
                (250, 230, 200),                                   # 5 cat cream
                (36, 30, 44), (70, 60, 84), (110, 100, 130)],      # 6-8 note black/purple
               [(250, 200, 90), (220, 120, 50), (150, 60, 30), (250, 240, 200)])  # 10-13 pick
    pb = [MAGENTA, OUT, (46, 44, 54), (82, 80, 94), (30, 28, 36),  # 2-4 tolex
          (66, 60, 66), (100, 92, 100),                            # 5-6 grill
          (210, 176, 120), (170, 136, 86),                         # 7-8 tweed panel
          (196, 196, 206), (240, 200, 60),                         # 9 chrome, 10 jewel light
          (220, 60, 50), (250, 250, 240), (36, 30, 40),            # 11 red, 12 white, 13 black
          (150, 150, 160), (90, 220, 240)]                         # 14 grey, 15 cyan
    big = [cat(f) for f in ("walk0", "walk1", "walk2", "walk3", "charge0", "charge1", "hurt")]
    big += [walking_amp(f) for f in ("walk0", "walk1", "walk2", "walk3", "charge0", "charge1", "hurt")]
    small = [pick(0), pick(1), spark(0), spark(1), spark(2), heart(),
             note("walk0"), note("walk1"), note("alt0"), note("alt1"), flash(note("walk0"), keep=(1,)),
             sound_wave(0), sound_wave(1)]
    boss = [amp_stack(f) for f in ("idle0", "idle1", "attack", "hurt")]
    return pa, pb, AMP_PAL, big, small, boss


def pick(i):
    c = Canvas(16, 16)
    pts = [(8, 13), (3, 5), (13, 5)] if i == 0 else [(3, 8), (11, 3), (11, 13)]
    for y in range(16):
        for x in range(16):
            (x0, y0), (x1, y1), (x2, y2) = pts
            d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            a = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / d
            b = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / d
            if a >= -0.05 and b >= -0.05 and 1 - a - b >= -0.05:
                c.set(x, y, 11)
    shade(c, 11, 10, 12)
    c.set(8 if i == 0 else 9, 7 if i == 0 else 8, 13)
    return outlined(c, 1)


def cat(frame):
    walk = frame.startswith("walk")
    charge = frame.startswith("charge")
    i = int(frame[-1]) if frame[-1].isdigit() else 0
    by = 23 + (1 if walk and i in (1, 3) else 0)
    stretch = 3 if charge and i == 1 else 0
    legs_far, legs = Canvas(32, 32), Canvas(32, 32)
    sw = ([2, 0, -2, 0][i] if walk else ([4, -4][i] if charge else 0))
    for (hx, s, layer) in ((9, sw, legs_far), (20 + stretch, -sw, legs_far), (11, -sw, legs), (22 + stretch, sw, legs)):
        capsule(layer, (hx, by + 1), (hx + s * 0.6, 30), 1.1, 3 if layer is legs_far else 2)
        layer.set(int(hx + s * 0.6), 30, 5)
    body = Canvas(32, 32)
    capsule(body, (9, by - 1), (21 + stretch, by - 1 - (2 if charge else 0)), 4, 2)
    for x in range(11, 20 + stretch, 3):                 # tabby stripes
        capsule(body, (x, by - 4), (x + 1, by - 1), 0.4, 4)
    capsule(body, (8, by - 2), (3, by - 10 + (3 if charge else 0)), 1.2, 2)   # tail
    capsule(body, (3, by - 10 + (3 if charge else 0)), (5, by - 14 + (4 if charge else 0)), 1.2, 3)
    head = Canvas(32, 32)
    hx, hy = 25 + stretch, by - 6 + (3 if charge else 0)
    ellipse(head, hx, hy, 4.5, 4, 2)
    capsule(head, (hx - 3, hy - 3), (hx - 3, hy - 7), 1, 2)  # ears
    capsule(head, (hx + 2, hy - 3), (hx + 2, hy - 7), 1, 2)
    ellipse(head, hx + 2, hy + 1.5, 2.2, 1.6, 5)
    head.set(int(hx + 1), int(hy - 1), 9 if not charge else 15)
    head.set(int(hx + 3), int(hy - 1), 9 if not charge else 15)
    head.set(int(hx + 4), int(hy + 1), 15)
    shade(body, 2, None, 3)
    out = compose(legs_far, body, legs, head)
    out = feet_down(out)
    if frame == "hurt":
        out = flash(out)
    return out


def note(frame):
    """A sour music note with an angry face, flapping a flag."""
    c = Canvas(16, 16)
    alt = frame.startswith("alt")
    i = int(frame[-1])
    ellipse(c, 6, 11, 4, 3, 6)
    capsule(c, (9.5, 11), (9.5, 2), 0.8, 6)
    if (i == 0) != alt:
        capsule(c, (10, 2), (14, 6), 1, 7)
    else:
        capsule(c, (10, 2), (14, 3), 1, 7)
    c.set(4, 10, 9); c.set(7, 10, 9)                    # angry eyes
    c.set(5, 12, 15)
    shade(c, 6, 7, 6)
    return outlined(c, 1)


def walking_amp(frame):
    walk = frame.startswith("walk")
    charge = frame.startswith("charge")
    i = int(frame[-1]) if frame[-1].isdigit() else 0
    bob = 1 if walk and i in (1, 3) else 0
    legs = Canvas(32, 32)
    sw = ([2, 0, -2, 0][i] if walk else ([3, -3][i] if charge else 0))
    capsule(legs, (11, 24), (11 + sw, 30), 1.4, 4)
    capsule(legs, (21, 24), (21 - sw, 30), 1.4, 4)
    capsule(legs, (10 + sw, 31), (13 + sw, 31), 1, 13)
    capsule(legs, (20 - sw, 31), (23 - sw, 31), 1, 13)
    box = Canvas(32, 32)
    top = 4 + bob - (2 if charge else 0)
    for y in range(top, 25 + bob):
        for x in range(5, 28):
            box.set(x, y, 2)
    for y in range(top + 2, top + 6):
        for x in range(7, 26):
            box.set(x, y, 7)
    for kx in range(9, 24, 3):
        box.set(kx, top + 4, 9)
    box.set(24, top + 3, 11 if charge else 10)
    for y in range(top + 8, 23 + bob):
        for x in range(7, 26):
            box.set(x, y, 5 if (x + y) % 3 else 6)
    # speaker face: eyes and a growling grille mouth
    ellipse(box, 12, top + 12, 2, 2, 12); box.set(12, top + 12, 13)
    ellipse(box, 21, top + 12, 2, 2, 12); box.set(21, top + 12, 13)
    for x in range(11, 23):
        box.set(x, top + 17, 13 if not charge else 11)
    out = compose(legs, box)
    out = feet_down(out)
    if frame == "hurt":
        out = flash(out, to=12)
    return out


AMP_PAL = [MAGENTA, OUT,
           (46, 44, 54), (82, 80, 94), (28, 26, 34),            # 2-4 tolex
           (66, 60, 66), (100, 92, 100),                        # 5-6 grill
           (210, 176, 120), (170, 136, 86),                     # 7-8 tweed
           (196, 196, 206),                                     # 9 chrome
           (90, 220, 240), (190, 250, 255),                     # 10-11 sound cyan
           (240, 80, 150),                                      # 12 pink glow
           (250, 210, 80),                                      # 13 yellow light
           (248, 248, 240), (224, 56, 56)]


def sound_wave(i):
    c = Canvas(16, 16)
    for k, r in enumerate((3, 6) if i == 0 else (4, 7)):
        for a in range(-50, 51, 5):
            x = 4 + math.cos(math.radians(a)) * r
            y = 8 + math.sin(math.radians(a)) * r
            c.set(int(x), int(y), 10 if k == 0 else 11)
            c.set(int(x) + 1, int(y), 10)
    return c


def amp_stack(frame):
    attack = frame == "attack"
    c = Canvas(64, 64)
    body = Canvas(64, 64)
    bob = 1 if frame == "idle1" else 0
    # two stacked cabinets and a head on top, slightly leaning when firing
    for (x0, y0, x1, y1) in ((6, 36, 58, 63), (6, 12 + bob, 58, 36), (10, 2 + bob, 54, 12 + bob)):
        for y in range(y0, y1):
            for x in range(x0, x1):
                body.set(x, y, 2)
    for x in range(10, 54):
        for y in range(4 + bob, 10 + bob):
            body.set(x, y, 7)
    for kx in range(14, 50, 5):
        body.set(kx, 7 + bob, 9); body.set(kx, 8 + bob, 4)
    body.set(48, 6 + bob, 12 if attack else 13)
    for (cx, cy) in ((20, 24 + bob), (44, 24 + bob), (20, 50), (44, 50)):
        ellipse(body, cx, cy, 9, 9, 5)
        ellipse(body, cx, cy, 6, 6, 6)
        r = 4 if not attack else 5
        ellipse(body, cx, cy, r, r, 4)
        ellipse(body, cx, cy, 1.5, 1.5, 9)
    # angry face across the top cabinet: brows over the speakers
    capsule(body, (12, 13 + bob), (26, 17 + bob), 1, 1)
    capsule(body, (52, 13 + bob), (38, 17 + bob), 1, 1)
    for (x, y) in ((1, 1), (62, 1), (1, 62), (62, 62)):
        body.set(x, y, 9)
    out = compose(body, size=64)
    if attack:
        for k in range(3):                               # feedback bolts
            x0 = 30 + k * 2
            pts = [(x0, 0), (x0 - 4, 5), (x0 + 2, 7), (x0 - 2, 12)]
            for a, b in zip(pts, pts[1:]):
                capsule(out, a, b, 0.5, 10 + (k % 2))
    if frame == "hurt":
        out = flash(out, keep=(1,), to=14)
    return out


# ================================================================== STAGE 3
PUNK_HEAD = [
    "....MM......",
    "...MMMM.....",
    "..oMMMMoo...",
    ".oHMMHHHHo..",
    "oHHHHSSSSSo.",
    "oHHsSSoSoSo.",
    "oHsdSSoSoSo.",
    ".osdSSSSSSo.",
    ".odsSSorrro.",
    "..oddSSSoo..",
    "...ooooo....",
]
PUNK_TORSO = [
    ".oJJJJo..",
    "oJJTTTJJo",
    "oJJTTTTJo",
    "oJJTTTTJJo",
    "oJsJTTTJJo",
    "oJJJTTTJJo",
    "oJJJJJJJJo",
    ".oooooooo.",
]


def stage3():
    pa = pal_a([(120, 220, 80),                                    # 2 placeholder (skin set below)
                (0, 0, 0), (0, 0, 0),
                (100, 230, 90),                                    # 5 mohawk green
                (34, 30, 40), (70, 66, 80),                        # 6-7 leather black/grey
                (60, 70, 120)],                                    # 8 jeans
               [(220, 220, 230), (170, 170, 184), (120, 120, 134), (250, 210, 80)])   # bottle cap
    pa[2:5] = SKIN
    pb = [MAGENTA, OUT, *SKIN,
          (120, 80, 50), (160, 110, 70),                           # 5-6 hair
          (240, 120, 160), (200, 80, 120), (250, 170, 200),        # 7-9 pink polo
          (200, 180, 130), (170, 150, 100), (130, 110, 70),        # 10-12 khaki shorts
          (60, 50, 50), (248, 248, 240), (220, 50, 50)]            # 13 shoes, 14 white, 15 red cup
    punk = humanoid("punk", pa, PUNK_HEAD, {"o": 1, "S": 2, "s": 3, "d": 4, "H": 6, "M": 5, "r": 15},
                    PUNK_TORSO, {"o": 1, "J": 6, "T": 15, "s": 9},
                    dict(leg=(8, None, 6), sleeve=(6, 7, 6), shoe=6, steel=10,
                         torso_shade=(6, 7, 6), head_top=0, hip_y=19))
    frat = humanoid("frat", pb, FRAT_HEAD, {"o": 1, "S": 2, "s": 3, "d": 4, "H": 5, "C": 13, "B": 13, "w": 14},
                    FRAT_TORSO, {"o": 1, "P": 7, "p": 8, "c": 14},
                    dict(leg=(10, 11, 12), sleeve=(7, 9, 8), shoe=13, steel=15,
                         torso_shade=(7, 9, 8), head_top=1))
    big = humanoid_frames(punk) + humanoid_frames(frat)
    small = [bottle_cap(0), bottle_cap(1), spark(0), spark(1), spark(2), heart(),
             rat("walk0"), rat("walk1"), rat("alt0"), rat("alt1"), flash(rat("walk0")),
             bottle(0), bottle(1)]
    boss = [bouncer(f) for f in ("idle0", "idle1", "attack", "hurt")]
    return pa, pb, BOUNCER_PAL, big, small, boss


FRAT_HEAD = [
    "..oooooo....",
    ".oCCCCCCo...",
    "oBBCCCCCCo..",
    "oBoHHHHHHo..",
    "oHHHHSSSSSo.",
    "oHHsSSoSoSo.",
    "oHsdSSoSoSo.",
    ".osdSSSSSSo.",
    ".odsSSowwwo.",
    "..oddSSSoo..",
    "...ooooo....",
]
FRAT_TORSO = [
    ".occcco..",
    "oPPccPPPo",
    "oPPPPPPPo",
    "oPPPPPPPPo",
    "oPPPPPPPPo",
    "oPPPPPPPPo",
    "opppppppPo",
    ".oooooooo.",
]


def bottle_cap(i):
    c = Canvas(16, 16)
    if i == 0:
        ellipse(c, 8, 8, 4, 4, 11)
        for a in range(0, 360, 30):
            c.set(int(8 + math.cos(math.radians(a)) * 4.6), int(8 + math.sin(math.radians(a)) * 4.6), 12)
        ellipse(c, 8, 8, 2, 2, 10)
        c.set(7, 7, 13)
    else:
        for x in range(4, 13):
            c.set(x, 7, 11); c.set(x, 8, 12)
        for x in range(4, 13, 2):
            c.set(x, 9, 12)
    return outlined(c, 1)


def rat(frame):
    c = Canvas(16, 16)
    alt = frame.startswith("alt")
    i = int(frame[-1])
    ellipse(c, 7, 11, 4.5, 2.8, 7)
    ellipse(c, 12, 10, 2.5, 2, 7)
    c.set(15, 10, 15); c.set(12, 9, 1)
    ellipse(c, 10, 8, 1.2, 1.2, 15)                       # ear
    tail = (1, 9 - (2 if alt else 0))
    capsule(c, (3, 11), tail, 0.4, 15)
    sw = 1 if (i == 0) != alt else -1
    c.set(5 + sw, 14, 6); c.set(9 - sw, 14, 6)
    shade(c, 7, None, 6)
    return outlined(c, 1)


BOUNCER_PAL = [MAGENTA, OUT, *SKIN,
               (30, 30, 36), (56, 56, 66), (84, 84, 98),              # 5-7 black tee
               (40, 40, 48),                                          # 8 jeans dark
               (240, 240, 230),                                       # 9 STAFF text
               (60, 140, 70), (120, 200, 120), (30, 90, 40),          # 10-12 bottle green
               (24, 24, 30),                                          # 13 sunglasses
               (248, 248, 240), (224, 56, 56)]


def bottle(i):
    c = Canvas(16, 16)
    if i == 0:
        capsule(c, (4, 11), (10, 5), 2, 10)
        capsule(c, (10, 5), (13, 2), 0.8, 10)
        shade(c, 10, 11, 12)
    else:
        capsule(c, (4, 5), (10, 11), 2, 10)
        capsule(c, (10, 11), (13, 14), 0.8, 10)
        shade(c, 10, 11, 12)
    return outlined(c, 1)


def bouncer(frame):
    attack = frame == "attack"
    bob = 1 if frame == "idle1" else 0
    legs = Canvas(64, 64)
    capsule(legs, (24, 42), (22, 61), 5, 8)
    capsule(legs, (40, 42), (42, 61), 5, 8)
    capsule(legs, (18, 62), (27, 62), 2, 5)
    capsule(legs, (38, 62), (47, 62), 2, 5)
    torso = Canvas(64, 64)
    ellipse(torso, 32, 30 + bob, 19, 15, 5)              # barrel chest
    for y in range(36, 46):
        for x in range(17, 48):
            torso.set(x, y + bob, 5)
    shade(torso, 5, 6, 5)
    for k, x in enumerate(range(24, 41, 4)):              # STAFF lettering blocks
        for y in range(25 + bob, 28 + bob):
            torso.set(x, y, 9); torso.set(x + 1, y, 9)
    head = Canvas(64, 64)
    ellipse(head, 32, 12 + bob, 9, 10, 2)
    shade(head, 2, None, 3)
    ellipse(head, 22, 16 + bob, 2, 3, 3); ellipse(head, 42, 16 + bob, 2, 3, 3)    # ears
    for x in range(25, 40):                                # sunglasses
        head.set(x, 11 + bob, 13); head.set(x, 12 + bob, 13)
    head.set(28, 11 + bob, 14); head.set(36, 11 + bob, 14)
    for x in range(28, 37):
        head.set(x, 18 + bob, 4)                            # frown
    head.set(32, 4 + bob, 14)                               # shine on the bald head
    arms = Canvas(64, 64)
    if attack:
        capsule(arms, (14, 22), (6, 10), 4, 6)              # wind up to throw
        ellipse(arms, 6, 8, 4, 4, 3)
        capsule(arms, (50, 22), (56, 36), 4, 6)
        ellipse(arms, 56, 38, 4, 4, 3)
    else:
        capsule(arms, (14, 24 + bob), (44, 34 + bob), 4.5, 6)   # crossed arms
        capsule(arms, (50, 24 + bob), (20, 34 + bob), 4.5, 7)
        ellipse(arms, 46, 34 + bob, 3.5, 3.5, 3)
        ellipse(arms, 18, 34 + bob, 3.5, 3.5, 3)
    out = compose(legs, torso, head, arms, size=64)
    out = feet_down(out)
    if frame == "hurt":
        out = flash(out, keep=(1, 13))
    return out


# ================================================================== STAGE 4
GUARD_HEAD = [
    "..oooooo....",
    ".oKKKKKKo...",
    "oKKKbKKKKo..",
    "oKKKKKKKKKKo",
    "oHHHHSSSSSo.",
    "oHHsSSoSoSo.",
    "oHsdSSoSoSo.",
    ".osdSSSSSSo.",
    ".odsSSoooSo.",
    "..oddSSSoo..",
    "...ooooo....",
]
GUARD_TORSO = [
    ".oVVVVo..",
    "oVVKKVVVo",
    "oVVKKVVVo",
    "oVwwwwwwVo",
    "oVVKKVVVVo",
    "oVwwwwwwVo",
    "oKKKKKKKKo",
    ".oooooooo.",
]


def stage4():
    pa = pal_a([(0, 0, 0), (0, 0, 0), (0, 0, 0),
                (250, 220, 60),                                    # 5 hi-vis yellow
                (40, 44, 60), (70, 76, 96),                        # 6-7 navy
                (150, 150, 170)],                                  # 8 pigeon grey
               [(250, 210, 120), (220, 160, 70), (170, 60, 40), (230, 60, 50)])   # deep dish slice
    pa[2:5] = SKIN
    pb = [MAGENTA, OUT,
          (240, 170, 120), (210, 130, 80), (160, 90, 50),          # 2-4 bun
          (170, 80, 60), (130, 56, 44), (90, 36, 30),              # 5-7 sausage
          (250, 210, 60), (60, 170, 80),                           # 8 mustard, 9 relish
          (240, 240, 232), (40, 40, 48),                           # 10 white, 11 black
          (252, 208, 168), (228, 164, 124),                        # 12-13 arms skin
          (90, 90, 110), (224, 56, 56)]
    guard = humanoid("guard", pa, GUARD_HEAD, {"o": 1, "S": 2, "s": 3, "d": 4, "H": 6, "K": 6, "b": 9},
                     GUARD_TORSO, {"o": 1, "V": 5, "K": 6, "w": 14},
                     dict(leg=(6, 7, 6), sleeve=(6, 7, 6), shoe=1, steel=14,
                          torso_shade=(5, 14, 5), head_top=1))
    big = humanoid_frames(guard)
    big += [hotdog(f) for f in ("walk0", "walk1", "walk2", "walk3", "charge0", "charge1", "hurt")]
    small = [pizza(0), pizza(1), spark(0), spark(1), spark(2), heart(),
             pigeon("walk0"), pigeon("walk1"), pigeon("alt0"), pigeon("alt1"), flash(pigeon("walk0")),
             feather(0), feather(1)]
    boss = [pigeon_king(f) for f in ("idle0", "idle1", "attack", "hurt")]
    return pa, pb, PIGEON_PAL, big, small, boss


def pizza(i):
    c = Canvas(16, 16)
    pts = [(2, 4), (14, 6), (5, 14)] if i == 0 else [(4, 2), (12, 13), (2, 11)]
    for y in range(16):
        for x in range(16):
            (x0, y0), (x1, y1), (x2, y2) = pts
            d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            a = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / d
            b = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / d
            if a >= -0.05 and b >= -0.05 and 1 - a - b >= -0.05:
                c.set(x, y, 13)
    capsule(c, pts[0], pts[1], 1.2, 10)                    # crust
    for (x, y) in ((7, 7), (9, 9), (6, 10)) if i == 0 else ((6, 6), (8, 9), (5, 9)):
        c.set(x, y, 12)
    return outlined(c, 1)


def pigeon(frame):
    c = Canvas(16, 16)
    alt = frame.startswith("alt")
    i = int(frame[-1])
    ellipse(c, 8, 9, 4.5, 3.2, 8)
    ellipse(c, 12, 5, 2.3, 2.3, 8)
    c.set(14, 5, 9); c.set(15, 5, 9)
    c.set(12, 4, 1)
    ellipse(c, 11, 8, 1.5, 1.5, 7)                         # iridescent neck
    capsule(c, (4, 9), (1, 7), 0.8, 7)
    wing = Canvas(16, 16)
    up = (i == 0) != alt
    capsule(wing, (7, 8), (4, 2) if up else (3, 12), 1.4, 7)
    shade(c, 8, 14, 7)
    out = Canvas(16, 16)
    out.blit(outlined(c, 1))
    out.blit(outlined(wing, 1))
    if not alt:
        out.set(7, 13, 15); out.set(9, 13, 15)
    return out


def feather(i):
    c = Canvas(16, 16)
    a, b = ((4, 12), (12, 4)) if i == 0 else ((4, 4), (12, 12))
    capsule(c, a, b, 2, 7)
    capsule(c, a, b, 0.4, 10)
    return outlined(c, 1)


def hotdog(frame):
    walk = frame.startswith("walk")
    charge = frame.startswith("charge")
    i = int(frame[-1]) if frame[-1].isdigit() else 0
    bob = 1 if walk and i in (1, 3) else 0
    legs = Canvas(32, 32)
    sw = ([2, 0, -2, 0][i] if walk else ([3, -3][i] if charge else 0))
    capsule(legs, (13, 26), (13 + sw, 30), 1.4, 12)
    capsule(legs, (19, 26), (19 - sw, 30), 1.4, 12)
    capsule(legs, (12 + sw, 31), (15 + sw, 31), 1, 11)
    capsule(legs, (18 - sw, 31), (21 - sw, 31), 1, 11)
    bun = Canvas(32, 32)
    capsule(bun, (16, 6 + bob), (16, 26 + bob), 7, 3)
    shade(bun, 3, 2, 4)
    dog = Canvas(32, 32)
    capsule(dog, (16, 2 + bob), (16, 28 + bob), 4, 6)
    shade(dog, 6, 5, 7)
    for y in range(6, 26, 4):                              # mustard zigzag
        dog.set(15, y + bob, 8); dog.set(17, y + 2 + bob, 8); dog.set(16, y + 1 + bob, 8)
    face = Canvas(32, 32)
    face.set(14, 10 + bob, 10); face.set(18, 10 + bob, 10)
    face.set(14, 11 + bob, 11); face.set(18, 11 + bob, 11)
    for x in range(14, 19):
        face.set(x, 14 + bob, 11)
    arms = Canvas(32, 32)
    if charge:
        capsule(arms, (10, 14), (4, 8), 1.2, 12)
        capsule(arms, (22, 14), (28, 8), 1.2, 12)
    else:
        capsule(arms, (10, 14 + bob), (6, 20 + bob), 1.2, 12)
        capsule(arms, (22, 14 + bob), (26, 20 + bob), 1.2, 12)
    out = compose(legs, bun, arms)
    out.blit(dog)
    out.blit(face)
    out = feet_down(out)
    if frame == "hurt":
        out = flash(out, to=10)
    return out


PIGEON_PAL = [MAGENTA, OUT,
              (170, 170, 190), (130, 130, 150), (96, 96, 116),         # 2-4 grey body
              (110, 170, 150), (150, 100, 170),                        # 5-6 iridescent neck
              (230, 230, 240),                                         # 7 wing bars light
              (250, 200, 60), (200, 140, 30),                          # 8-9 gold crown
              (224, 56, 56),                                           # 10 jewel red / eye
              (240, 150, 70),                                          # 11 feet orange
              (60, 60, 76),                                            # 12 dark tips
              (230, 220, 200), (248, 248, 240), (224, 56, 56)]         # 13 bread, 14 white


def pigeon_king(frame):
    attack = frame == "attack"
    flap = frame == "idle1"
    body = Canvas(64, 64)
    ellipse(body, 30, 36, 20, 14, 2)
    ellipse(body, 44, 20, 10, 10, 2)                      # head
    ellipse(body, 40, 28, 8, 7, 5)                        # neck sheen
    ellipse(body, 36, 31, 5, 4, 6)
    capsule(body, (11, 38), (2, 34), 3, 3)                # tail
    shade(body, 2, 7, 3)
    beak = Canvas(64, 64)
    capsule(beak, (52, 20 + (3 if attack else 0)), (59, 22 + (4 if attack else 0)), 1.6, 9)
    ellipse(beak, 51, 17, 2.5, 1.5, 13)
    body.set(47, 17, 10); body.set(48, 17, 1)             # angry red eye
    wing = Canvas(64, 64)
    if flap:
        capsule(wing, (28, 30), (12, 6), 5, 3)
        capsule(wing, (12, 6), (4, 2), 3, 12)
    elif attack:
        capsule(wing, (28, 30), (18, 50), 5, 3)
        capsule(wing, (18, 50), (12, 58), 3, 12)
    else:
        capsule(wing, (24, 32), (6, 40), 6, 3)
        capsule(wing, (6, 40), (2, 44), 3, 12)
    for k in range(3):
        capsule(wing, (20 - k * 4, 34 + k), (14 - k * 4, 38 + k), 0.6, 7)
    feet = Canvas(64, 64)
    for fx in (26, 36):
        capsule(feet, (fx, 48), (fx, 58), 1.2, 11)
        capsule(feet, (fx - 3, 59), (fx + 4, 59), 1, 11)
    crown = Canvas(64, 64)
    for x in range(37, 52):
        for y in range(6, 10):
            crown.set(x, y, 8)
    for x in (37, 42, 47, 51):
        capsule(crown, (x, 6), (x, 2), 0.8, 8)
        crown.set(x, 1, 10)
    shade(crown, 8, None, 9)
    out = compose(feet, body, wing, beak, crown, size=64)
    if frame == "hurt":
        out = flash(out, keep=(1, 8, 9))
    return out


# ================================================================== STAGE 5
def stage5():
    pa = pal_a([(220, 210, 60), (170, 160, 40), (110, 100, 30),     # 2-4 buffer yellow
                (90, 90, 100), (50, 50, 60),                       # 5-6 metal / bat dark
                (140, 70, 140), (90, 40, 96)],                     # 7-8 bat purple
               [(220, 250, 255), (150, 210, 240), (90, 150, 210), (250, 200, 240)])   # soap bubble
    pb = [MAGENTA, OUT,
          (210, 214, 226), (160, 166, 182), (110, 114, 130),       # 2-4 steel
          (240, 244, 250),                                         # 5 glint
          (70, 74, 90),                                            # 6 visor dark
          (170, 40, 44), (120, 26, 34),                            # 7-8 plume red
          (230, 190, 90), (180, 136, 54),                          # 9-10 gold trim
          (140, 100, 70), (100, 70, 50),                           # 11-12 wood (halberd)
          (36, 36, 44), (248, 248, 240), (224, 56, 56)]
    big = [buffer(f) for f in ("walk0", "walk1", "walk2", "walk3", "charge0", "charge1", "hurt")]
    big += [armor(f) for f in ("walk0", "walk1", "walk2", "walk3", "charge0", "charge1", "hurt")]
    small = [bubble(0), bubble(1), spark(0), spark(1), spark(2), heart(),
             bat("walk0"), bat("walk1"), bat("alt0"), bat("alt1"), flash(bat("walk0")),
             gavel(0), gavel(1)]
    boss = [judge(f) for f in ("idle0", "idle1", "attack", "hurt")]
    return pa, pb, JUDGE_PAL, big, small, boss


def bubble(i):
    c = Canvas(16, 16)
    r = 4 if i == 0 else 4.5
    ellipse(c, 8, 8, r, r, 11)
    ellipse(c, 8, 8, r - 1.2, r - 1.2, 0)
    for x in range(16):
        for y in range(16):
            if c.px[y][x] == 0 and (x - 8) ** 2 + (y - 8) ** 2 < (r - 1.2) ** 2:
                if (x + y) % 3 == 0:
                    c.set(x, y, 10)
    c.set(6, 5, 14); c.set(5, 6, 14); c.set(10, 10, 13)
    return c


def buffer(frame):
    """Runaway floor buffer: round machine with a long handle, spinning pad."""
    walk = frame.startswith("walk") or frame.startswith("charge")
    i = int(frame[-1]) if frame[-1].isdigit() else 0
    c = Canvas(32, 32)
    pad = Canvas(32, 32)
    ellipse(pad, 16, 28, 13, 3, 6)
    for x in range(4, 29):
        if (x + i * 3) % 6 < 2:
            pad.set(x, 29, 5)
    body = Canvas(32, 32)
    ellipse(body, 16, 22, 11, 6, 2)
    for x in range(5, 28):
        body.set(x, 24, 4)
    shade(body, 2, None, 3)
    body.set(10, 20, 15 if frame.startswith("charge") else 9)
    handle = Canvas(32, 32)
    lean = -2 if frame.startswith("charge") else 0
    capsule(handle, (12, 18), (5 + lean, 3), 0.9, 5)
    capsule(handle, (2 + lean, 3), (9 + lean, 2), 1, 6)
    cord = Canvas(32, 32)
    capsule(cord, (6, 6), (1, 20 + (i % 2)), 0.4, 6)
    out = compose(cord, handle, pad, body)
    if frame.startswith("charge"):
        for (x, y) in ((28, 30), (30, 28), (31, 31)):
            out.set(x, y, 11)                              # suds flying
    out = feet_down(out)
    if frame == "hurt":
        out = flash(out)
    return out


def armor(frame):
    walk = frame.startswith("walk")
    charge = frame.startswith("charge")
    i = int(frame[-1]) if frame[-1].isdigit() else 0
    bob = 1 if walk and i in (1, 3) else 0
    sw = ([2, 0, -2, 0][i] if walk else ([3, -3][i] if charge else 0))
    legs = Canvas(32, 32)
    capsule(legs, (13, 20), (13 + sw, 30), 1.9, 3)
    capsule(legs, (19, 20), (19 - sw, 30), 1.9, 2)
    capsule(legs, (12 + sw, 31), (16 + sw, 31), 1.2, 4)
    capsule(legs, (18 - sw, 31), (22 - sw, 31), 1.2, 3)
    shade(legs, 2, 5, 4)
    body = Canvas(32, 32)
    for y in range(9 + bob, 21 + bob):
        half = 6 - (y - 9 - bob) // 4
        for x in range(16 - half, 17 + half):
            body.set(x, y, 2)
    for x in range(11, 22):
        body.set(x, 20 + bob, 9)
    shade(body, 2, 5, 3)
    helm = Canvas(32, 32)
    ellipse(helm, 16, 6 + bob, 4.5, 5, 2)
    for x in range(13, 21):
        helm.set(x, 6 + bob, 6)                             # visor slit
    helm.set(18, 6 + bob, 15 if charge else 9)
    capsule(helm, (14, 1 + bob), (10, -2 + bob), 1.4, 7)    # plume
    shade(helm, 2, 5, 3)
    weapon = Canvas(32, 32)
    hx = 24 + (3 if charge else 0)
    capsule(weapon, (hx, 2 + bob), (hx - (4 if charge else 0), 30), 0.7, 11)
    capsule(weapon, (hx - 2, 4 + bob), (hx + 3, 2 + bob), 1.4, 3)    # axe head
    capsule(weapon, (hx, 0 + bob), (hx, 3 + bob), 0.6, 5)
    arm = Canvas(32, 32)
    capsule(arm, (19, 11 + bob), (hx, 15 + bob), 1.6, 3)
    out = compose(legs, body, helm, weapon, arm)
    out = feet_down(out)
    if frame == "hurt":
        out = flash(out, to=5)
    return out


def bat(frame):
    c = Canvas(16, 16)
    alt = frame.startswith("alt")
    i = int(frame[-1])
    ellipse(c, 8, 8, 2.6, 3, 8)
    c.set(6, 4, 8); c.set(10, 4, 8)
    c.set(7, 7, 15); c.set(9, 7, 15)
    up = (i == 0) != alt
    for side in (-1, 1):
        if up:
            pts = [(8 + side * 2, 8), (8 + side * 5, 3), (8 + side * 7, 5)]
        else:
            pts = [(8 + side * 2, 8), (8 + side * 5, 11), (8 + side * 7, 9)]
        for a, b in zip(pts, pts[1:]):
            capsule(c, a, b, 1.1, 7)
    return outlined(c, 1)


JUDGE_PAL = [MAGENTA, OUT, *SKIN,
             (36, 34, 44), (60, 58, 72), (90, 88, 106),              # 5-7 robe
             (240, 240, 236), (200, 200, 196), (160, 160, 158),      # 8-10 wig
             (140, 90, 56), (100, 60, 36),                           # 11-12 gavel wood
             (230, 190, 90),                                         # 13 brass
             (248, 248, 240), (224, 56, 56)]


def gavel(i):
    c = Canvas(16, 16)
    if i == 0:
        capsule(c, (3, 13), (9, 7), 0.8, 11)
        capsule(c, (7, 4), (13, 10), 2.2, 12)
        capsule(c, (7, 4), (13, 10), 1.0, 11)
    else:
        capsule(c, (3, 3), (9, 9), 0.8, 11)
        capsule(c, (6, 12), (12, 6), 2.2, 12)
        capsule(c, (6, 12), (12, 6), 1.0, 11)
    return outlined(c, 1)


def judge(frame):
    attack = frame == "attack"
    bob = 1 if frame == "idle1" else 0
    robe = Canvas(64, 64)
    for y in range(22 + bob, 64):
        half = 13 + (y - 22) * 0.35
        for x in range(int(32 - half), int(33 + half)):
            robe.set(x, y, 5)
    shade(robe, 5, 6, 5)
    for y in range(26 + bob, 62):
        robe.set(32, y, 7)
    for x in range(26, 39):                               # white collar
        robe.set(x, 22 + bob, 8); robe.set(x, 23 + bob, 8)
    head = Canvas(64, 64)
    ellipse(head, 32, 14 + bob, 7, 8, 2)
    shade(head, 2, None, 3)
    head.set(29, 13 + bob, 1); head.set(35, 13 + bob, 1)
    capsule(head, (27, 10 + bob), (31, 11 + bob), 0.6, 1)  # stern brows
    capsule(head, (37, 10 + bob), (33, 11 + bob), 0.6, 1)
    for x in range(29, 36):
        head.set(x, 18 + bob, 4)
    wig = Canvas(64, 64)
    for (cx, cy) in ((24, 10), (24, 15), (24, 20), (40, 10), (40, 15), (40, 20), (28, 5), (32, 4), (36, 5)):
        ellipse(wig, cx, cy + bob, 3.4, 3, 8)
    shade(wig, 8, None, 9)
    arms = Canvas(64, 64)
    if attack:
        capsule(arms, (44, 28), (54, 12), 3.5, 6)
        hand = (54, 10)
    else:
        capsule(arms, (44, 28 + bob), (52, 40 + bob), 3.5, 6)
        hand = (52, 42 + bob)
    ellipse(arms, hand[0], hand[1], 2.6, 2.6, 3)
    capsule(arms, (20, 28 + bob), (14, 42 + bob), 3.5, 6)
    ellipse(arms, 14, 44 + bob, 2.6, 2.6, 3)
    gv = Canvas(64, 64)
    if attack:
        capsule(gv, (hand[0], hand[1]), (hand[0] - 2, hand[1] - 10), 1, 11)
        capsule(gv, (hand[0] - 7, hand[1] - 12), (hand[0] + 3, hand[1] - 12), 3, 12)
    else:
        capsule(gv, (hand[0], hand[1]), (hand[0] + 8, hand[1] - 6), 1, 11)
        capsule(gv, (hand[0] + 6, hand[1] - 11), (hand[0] + 11, hand[1] - 3), 3, 12)
    out = compose(robe, arms, head, wig, gv, size=64)
    if frame == "hurt":
        out = flash(out, keep=(1,))
    return out


# ================================================================== STAGE 6
def stage6():
    pa = pal_a([(240, 240, 232), (200, 200, 196), (150, 150, 150),  # 2-4 cart white
                (80, 160, 90), (50, 110, 60),                      # 5-6 cart green roof
                (250, 140, 60), (200, 90, 40)],                    # 7-8 bingo orange
               [(250, 250, 244), (220, 210, 200), (230, 120, 130), (200, 70, 90)])   # dentures
    pb = [MAGENTA, OUT,
          (240, 240, 232), (200, 200, 196), (150, 150, 150),       # 2-4 goose white
          (70, 70, 80), (40, 40, 48),                              # 5-6 neck black
          (250, 160, 50), (200, 110, 30),                          # 7-8 beak orange
          (130, 120, 110), (90, 84, 78),                           # 9-10 grey wing
          (224, 56, 56), (250, 210, 80),                           # 11 red, 12 yellow
          (150, 100, 70), (248, 248, 240), (224, 56, 56)]
    big = [golf_cart(f) for f in ("walk0", "walk1", "walk2", "walk3", "charge0", "charge1", "hurt")]
    big += [goose(f) for f in ("walk0", "walk1", "walk2", "walk3", "charge0", "charge1", "hurt")]
    small = [dentures(0), dentures(1), spark(0), spark(1), spark(2), heart(),
             bingo("walk0"), bingo("walk1"), bingo("alt0"), bingo("alt1"), flash(bingo("walk0")),
             clock(0), clock(1)]
    boss = [father_time(f) for f in ("idle0", "idle1", "attack", "hurt")]
    return pa, pb, TIME_PAL, big, small, boss


def dentures(i):
    c = Canvas(16, 16)
    ellipse(c, 8, 8, 5, 3.5, 12)
    for x in range(4, 13):
        c.set(x, 7 + (i % 2), 10)
        if x % 2 == 0:
            c.set(x, 6 + (i % 2), 10)
            c.set(x, 9 + (i % 2), 10)
    for x in range(4, 13, 2):
        c.set(x, 8, 11)
    c.set(6, 6, 13)
    return outlined(c, 1)


def golf_cart(frame):
    i = int(frame[-1]) if frame[-1].isdigit() else 0
    charge = frame.startswith("charge")
    c = Canvas(32, 32)
    roof = Canvas(32, 32)
    for x in range(4, 28):
        roof.set(x, 4, 5); roof.set(x, 5, 6)
    capsule(roof, (6, 6), (6, 20), 0.6, 4)
    capsule(roof, (26, 6), (24, 18), 0.6, 4)
    driver = Canvas(32, 32)
    ellipse(driver, 15, 12, 3, 3, 3)
    ellipse(driver, 15, 10, 3, 1.6, 2)                    # white hair
    driver.set(17, 12, 1)
    capsule(driver, (14, 15), (14, 20), 2, 6)
    body = Canvas(32, 32)
    for y in range(18, 27):
        for x in range(3, 30):
            body.set(x, y, 2)
    for x in range(22, 30):
        for y in range(14, 18):
            body.set(x - (y - 14), y, 2)
    shade(body, 2, None, 3)
    body.set(28, 20, 9 if not charge else 15)             # headlight
    wheels = Canvas(32, 32)
    for wx in (8, 24):
        ellipse(wheels, wx, 27, 3.5, 3.5, 6)
        wheels.set(wx + (1 if i % 2 else -1), 27, 4)
    out = compose(roof, driver, body, wheels)
    if charge:
        for (x, y) in ((1, 28), (0, 25), (2, 24)):
            out.set(x, y, 3)
    out = feet_down(out)
    if frame == "hurt":
        out = flash(out, to=14)
    return out


def goose(frame):
    walk = frame.startswith("walk")
    charge = frame.startswith("charge")
    i = int(frame[-1]) if frame[-1].isdigit() else 0
    bob = 1 if walk and i in (1, 3) else 0
    legs = Canvas(32, 32)
    sw = ([2, 0, -2, 0][i] if walk else ([3, -3][i] if charge else 0))
    capsule(legs, (13, 23), (13 + sw, 30), 0.7, 7)
    capsule(legs, (17, 23), (17 - sw, 30), 0.7, 8)
    capsule(legs, (12 + sw, 31), (15 + sw, 31), 0.8, 7)
    capsule(legs, (16 - sw, 31), (19 - sw, 31), 0.8, 8)
    body = Canvas(32, 32)
    ellipse(body, 14, 19 + bob, 9, 5.5, 2)
    capsule(body, (6, 17 + bob), (3, 14 + bob), 1.6, 2)
    shade(body, 2, None, 3)
    capsule(body, (9, 17 + bob), (18, 18 + bob), 2.4, 9)  # folded wing
    neck = Canvas(32, 32)
    if charge:   # neck stretched forward, hissing
        capsule(neck, (20, 17 + bob), (27, 13), 1.6, 5)
        ellipse(neck, 28, 12, 2.6, 2.2, 6)
        capsule(neck, (30, 12), (31, 11), 0.9, 7)
        capsule(neck, (30, 13), (31, 14), 0.9, 7)
        neck.set(28, 11, 11)
    else:
        capsule(neck, (20, 16 + bob), (22, 6 + bob), 1.5, 5)
        ellipse(neck, 23, 5 + bob, 2.6, 2.2, 6)
        capsule(neck, (25, 5 + bob), (28, 6 + bob), 1, 7)
        neck.set(23, 4 + bob, 14)
    out = compose(legs, body, neck)
    out = feet_down(out)
    if frame == "hurt":
        out = flash(out, to=14)
    return out


def bingo(frame):
    c = Canvas(16, 16)
    alt = frame.startswith("alt")
    i = int(frame[-1])
    squash = (i == 1) and not alt
    ellipse(c, 8, 9 if not squash else 10, 5.5, 5.5 if not squash else 4.5, 7)
    shade(c, 7, 9, 8)
    ellipse(c, 8, 9, 2.6, 2.6, 14)
    c.set(7, 9, 1); c.set(9, 9, 1)                        # little digits
    c.set(7, 8, 1); c.set(9, 10, 1)
    c.set(5, 6, 14)
    return outlined(c, 1)


TIME_PAL = [MAGENTA, OUT, *SKIN,
            (60, 50, 90), (90, 76, 130), (40, 32, 64),             # 5-7 robe purple
            (240, 240, 236), (200, 200, 200),                      # 8-9 beard
            (230, 190, 90), (180, 136, 54),                        # 10-11 brass
            (250, 230, 160),                                       # 12 sand
            (150, 210, 240),                                       # 13 glass
            (248, 248, 240), (224, 56, 56)]


def clock(i):
    c = Canvas(16, 16)
    ellipse(c, 8, 8, 5, 5, 10)
    ellipse(c, 8, 8, 3.8, 3.8, 14)
    capsule(c, (8, 8), (8, 5), 0.4, 1)
    if i == 0:
        capsule(c, (8, 8), (11, 8), 0.4, 1)
    else:
        capsule(c, (8, 8), (6, 10), 0.4, 1)
    c.set(8, 2, 11); c.set(7, 2, 11); c.set(9, 2, 11)
    return outlined(c, 1)


def father_time(frame):
    attack = frame == "attack"
    bob = 2 if frame == "idle1" else 0
    robe = Canvas(64, 64)
    for y in range(16 + bob, 58 + bob):
        half = 10 + (y - 16) * 0.32
        for x in range(int(30 - half), int(31 + half)):
            robe.set(x, y, 5)
    for x in range(14, 47):                                # tattered hem
        for y in range(56 + bob, 60 + bob - (x % 5 == 0) * 2):
            robe.set(x, y, 7 if x % 3 else 5)
    shade(robe, 5, 6, 7)
    hood = Canvas(64, 64)
    ellipse(hood, 30, 13 + bob, 10, 11, 7)
    ellipse(hood, 31, 14 + bob, 6.5, 7.5, 2)
    shade(hood, 2, None, 3)
    hood.set(28, 13 + bob, 1); hood.set(34, 13 + bob, 1)
    beard = Canvas(64, 64)
    for k in range(8):
        capsule(beard, (27 + k, 18 + bob), (25 + k * 1.2, 34 + bob + (k % 3) * 2), 1.2, 8)
    shade(beard, 8, None, 9)
    arms = Canvas(64, 64)
    if attack:
        capsule(arms, (40, 24 + bob), (54, 14 + bob), 3, 6)
        hand = (55, 12 + bob)
    else:
        capsule(arms, (40, 24 + bob), (48, 36 + bob), 3, 6)
        hand = (49, 38 + bob)
    ellipse(arms, hand[0], hand[1], 2.4, 2.4, 3)
    glass = Canvas(64, 64)                                  # the hourglass
    gx, gy = hand[0] - 1, hand[1] - 10
    for y in range(-6, 7):
        half = 1 + abs(y) * 0.6
        for x in range(int(gx - half), int(gx + half) + 1):
            glass.set(x, gy + y, 13)
    for y in range(1, 6):
        half = abs(y) * 0.5
        for x in range(int(gx - half), int(gx + half) + 1):
            glass.set(x, gy + y, 12)
    glass.set(gx, gy, 12)
    for x in range(gx - 5, gx + 6):
        glass.set(x, gy - 7, 10); glass.set(x, gy + 7, 10)
    staff = Canvas(64, 64)
    capsule(staff, (12, 6 + bob), (16, 62), 0.9, 11)
    ellipse(staff, 12, 5 + bob, 2.5, 2.5, 10)
    capsule(arms, (20, 26 + bob), (14, 34 + bob), 3, 6)
    out = compose(staff, robe, hood, beard, arms, glass, size=64)
    if frame == "hurt":
        out = flash(out, keep=(1,))
    return out


STAGES = [stage1, stage2, stage3, stage4, stage5, stage6]


def boss_quadrants(frames):
    """64x64 frames -> 32x32 quadrant frames in the order TL, TR, BL, BR."""
    out = []
    for f in frames:
        for q in range(4):
            qx, qy = (q % 2) * 32, (q // 2) * 32
            out.append([[f.px[qy + y][qx + x] for x in range(32)] for y in range(32)])
    return out


def write_stage(n, data):
    pa, pb, pboss, big, small, boss = data
    assert len(big) == 14 and len(small) == 13 and len(boss) == 4, (n, len(big), len(small), len(boss))
    sa = [snes_color(c) for c in pa]
    to_image(stack(big, 32), sa).save(os.path.join(SPR, f"st{n}_foes.png"))
    to_image(stack(small, 16), sa).save(os.path.join(SPR, f"st{n}_small.png"))
    to_image(stack(boss, 64), [snes_color(c) for c in pboss]).save(os.path.join(SPR, f"st{n}_boss.png"))
    # B preview with its own palette
    to_image(stack(big[7:], 32), [snes_color(c) for c in pb]).save(os.path.join(SPR, f"st{n}_foes_b.png"))
    open(os.path.join(BUILD, f"st{n}_foes.pic"), "wb").write(grid_pic([f.px for f in big], 32))
    open(os.path.join(BUILD, f"st{n}_small.pic"), "wb").write(grid_pic([f.px for f in small], 16))
    open(os.path.join(BUILD, f"st{n}_boss.pic"), "wb").write(grid_pic(boss_quadrants(boss), 32))
    for name, p in (("spra", pa), ("sprb", pb), ("boss", pboss)):
        assert len(p) == 16, (n, name, len(p))
        open(os.path.join(BUILD, f"st{n}_{name}.pal"), "wb").write(palette_bytes([snes_color(c) for c in p]))


def main():
    os.makedirs(BUILD, exist_ok=True)
    for n, fn in enumerate(STAGES, 1):
        write_stage(n, fn())
    print("foes written")


if __name__ == "__main__":
    main()
