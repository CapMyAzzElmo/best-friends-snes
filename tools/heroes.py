"""Generates Jon and Wes sprite sheets: 32x32 frames, facing right.

Heroes are about 30px (Jon) and 27px (Wes) tall so the stage has room to
breathe. Each frame is built from layered parts (limbs, torso, head) with
per-part outlines, so the front arm gets its own line where it crosses the
body, the way Mega Man X sprites read.

Output: art/sprites/<hero>.png, a 32 x (32 * frames) indexed PNG with a
16-colour SNES-ready palette (index 0 transparent).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, ascii_canvas, capsule, ellipse, shade, outlined, to_image, snes_color, rot

OUT = os.path.join(os.path.dirname(__file__), "..", "art", "sprites")

TRANSPARENT = (255, 0, 255)
OUTLINE = (20, 16, 28)
SKIN = [(252, 208, 168), (228, 164, 124), (180, 112, 88)]
WHITE = (248, 248, 240)

# frame order (must match src/main.c)
FRAMES = (["idle0", "idle1", "idle2", "idle3"] + [f"run{i}" for i in range(8)] +
          ["jump", "apex", "fall", "land", "throw0", "throw1", "throw2", "hurt", "cheer"])

# ---------------------------------------------------------------------------
# Jon: tall, dark brown hair, clean-shaven grin, black hoodie, ripped light jeans
JON_PAL = [TRANSPARENT, OUTLINE, *SKIN,
           (72, 44, 28), (112, 76, 44),               # 5,6 hair dark/light
           (28, 28, 38), (52, 52, 68), (84, 88, 110),  # 7,8,9 hoodie dark/mid/light
           (176, 200, 224), (128, 156, 192), (84, 104, 144),  # 10,11,12 jeans light/mid/dark
           (68, 52, 44),                               # 13 shoes
           WHITE,                                      # 14
           (184, 184, 196)]                            # 15 drawstrings / spoon steel

JON_HEAD = [
    "...oooooo..",
    "..oHHHhhHo.",
    ".oHHHhhHHHo",
    ".oHHHHHHHHo",
    "oHHHHHHSHHo",
    "oHHHHSSSSSo",
    "oHHsdSSoSoSo",
    "oHHsdSSoSoSo",
    ".oHssSSSSSSo",
    ".odssSSowwwo",
    "..oddSSSooo.",
    "...ooooo....",
]
JON_HEAD_LEGEND = {"o": 1, "S": 2, "s": 3, "d": 4, "H": 5, "h": 6, "w": 14}

JON_TORSO = [
    ".oHHHHo..",
    "oHHMMMMMo",
    "oHMMMMMMo",
    "oHMMMtMtMo",
    "oHMMMMMMMo",
    "oHMMppppMo",
    "oHMMMMMMMo",
    "oHHHHHHHHo",
    ".oooooooo.",
]
JON_TORSO_LEGEND = {"o": 1, "H": 7, "M": 8, "t": 15, "p": 7}

# ---------------------------------------------------------------------------
# Wes: shorter and sturdier, black cap with sky-blue brim, glasses,
# ginger goatee, charcoal button-up over a black tee
WES_PAL = [TRANSPARENT, OUTLINE, *SKIN,
           (148, 68, 36), (204, 116, 60),              # 5,6 goatee dark/light
           (30, 30, 40),                               # 7 cap / tee black
           (76, 78, 90), (108, 112, 126),              # 8,9 shirt mid/light
           (148, 204, 244), (88, 144, 204),            # 10,11 brim light/dark
           (60, 68, 100), (38, 44, 70),                # 12,13 pants mid/dark
           WHITE,                                      # 14
           (80, 60, 48)]                               # 15 shoes

WES_HEAD = [
    "...ooooo.....",
    "..oCCccCo....",
    ".oCCCCCCCoo..",
    ".oCCCCCCBBBBo",
    "oCCCCCBBbbbbo",
    "oCCsSSoooooo.",
    "oCsdSoLLoLLo.",
    "oCsdSSooSooo.",
    ".odsSGSSSSo..",
    ".odgGGooGGo..",
    "..ogGGGGGo...",
    "...oooooo....",
]
WES_HEAD_LEGEND = {"o": 1, "S": 2, "s": 3, "d": 4, "G": 5, "g": 6, "C": 7, "c": 8,
                   "B": 10, "b": 11, "L": 14}

WES_TORSO = [
    ".oMMMMo...",
    "oMMMTTTMo.",
    "oMMMMTTTMo",
    "oMMMMTTTMo",
    "oMMMMTTTMo",
    "oMMMMTTTMo",
    "oDDDDDDDDo",
    ".oooooooo.",
]
WES_TORSO_LEGEND = {"o": 1, "M": 8, "T": 7, "D": 13}


class Hero:
    def __init__(self, name, pal, head, head_legend, torso, torso_legend, spec):
        self.name, self.pal, self.spec = name, pal, spec
        self.head = ascii_canvas(head, head_legend)
        self.torso = ascii_canvas(torso, torso_legend)


# body layout inside the 32x32 cell; feet end on row 31
JON = Hero("jon", JON_PAL, JON_HEAD, JON_HEAD_LEGEND, JON_TORSO, JON_TORSO_LEGEND, dict(
    head_top=1, head_x=10, torso_x=11, torso_y=11, hip_y=19, shoulder_y=13,
    thigh=5.5, shin=5.5, upper=4.2, fore=4.0, leg_r=1.7, arm_r=1.35,
    leg=(11, 10, 12), sleeve=(8, 9, 7), shoe=13, steel=15, rip=10,
    torso_shade=(8, 9, 7), hand_in_pocket=True))

WES = Hero("wes", WES_PAL, WES_HEAD, WES_HEAD_LEGEND, WES_TORSO, WES_TORSO_LEGEND, dict(
    head_top=4, head_x=9, torso_x=11, torso_y=14, hip_y=21, shoulder_y=16,
    thigh=4.8, shin=4.8, upper=3.8, fore=3.6, leg_r=1.95, arm_r=1.55,
    leg=(12, None, 13), sleeve=(8, 9, 7), shoe=15, steel=14, rip=None,
    torso_shade=(8, 9, 7), hand_in_pocket=False))


def limb(r, color3, points):
    mid, light, dark = color3
    c = Canvas(32, 32)
    for a, b in zip(points, points[1:]):
        capsule(c, a, b, r, mid)
    shade(c, mid, light if light is not None else mid, dark)
    return c


def hand(pos, r=1.1):
    c = Canvas(32, 32)
    ellipse(c, pos[0], pos[1], r, r, 3)
    c.set(int(pos[0]), int(pos[1]), 2)
    return c


def shoe(foot, color):
    c = Canvas(32, 32)
    capsule(c, (foot[0] - 0.5, foot[1] + 0.3), (foot[0] + 2.2, foot[1] + 0.5), 1.15, color)
    return c


def run_leg(p):
    """Leg pose over the run cycle: thigh swings, knee folds as the foot comes back."""
    thigh = 42 * math.sin(p)
    # the knee folds while the thigh swings forward (the foot is off the
    # ground), and the leg straightens as it plants and pushes back
    bend = 14 + 70 * max(0.0, math.cos(p)) ** 1.3
    return thigh, bend


def pose(name):
    """(dx lean, bob, back_leg, front_leg, back_arm, front_arm).

    Legs: (thigh angle, knee bend). Arms: (upper angle, elbow bend).
    Angles in degrees from straight down; positive swings toward facing.
    """
    if name.startswith("idle"):
        i = int(name[4:])
        breathe = [0, 0, 1, 1][i]
        sway = [0, 2, 4, 2][i]
        return 0, breathe, (-6, 4), (8, 4), (-6 - sway, 14), (6 + sway, 20)
    if name.startswith("run"):
        i = int(name[3:])
        ph = i / 8 * 2 * math.pi
        bob = [0, 1, 1, 0, 0, 1, 1, 0][i]
        swing = 38 * math.sin(ph)
        # each arm swings against the leg on its own side
        return 1, bob, run_leg(ph + math.pi), run_leg(ph), (swing, 75), (-swing, 75)
    if name == "jump":
        return 1, -1, (-20, 30), (55, 95), (-50, 40), (60, 70)
    if name == "apex":
        return 0, -1, (-5, 50), (40, 80), (-80, 40), (90, 50)
    if name == "fall":
        return 0, 0, (-18, 15), (22, 30), (-110, 30), (120, 30)
    if name == "land":
        return 0, 2, (-30, -55), (35, 60), (-30, 40), (40, 40)
    if name == "throw0":   # spoon cocked back
        return -1, 0, (-14, 6), (18, 10), (-10, 30), (-100, -60)
    if name == "throw1":   # whip it over
        return 1, 1, (-20, 8), (24, 12), (-30, 20), (150, -20)
    if name == "throw2":   # follow through
        return 2, 1, (-24, 10), (26, 14), (-40, 20), (80, 10)
    if name == "hurt":
        return -2, 0, (-20, 30), (14, 20), (-150, 20), (95, 50)
    if name == "cheer":
        return 0, -1, (-8, 6), (10, 6), (-140, -20), (120, 40)
    raise ValueError(name)


SPOON = {"throw0": -50, "throw1": 20, "throw2": 70}


def draw_spoon(c, hand_pos, ang, steel):
    a = math.radians(ang)
    dx, dy = math.sin(a), -math.cos(a)
    tip = (hand_pos[0] + dx * 5, hand_pos[1] + dy * 5)
    capsule(c, hand_pos, tip, 0.6, steel)
    ellipse(c, tip[0] + dx * 1.3, tip[1] + dy * 1.3, 1.8, 1.8, steel)
    c.set(int(tip[0] + dx * 1.3), int(tip[1] + dy * 1.3), 14)


def frame(hero, name):
    s = hero.spec
    lean, bob, bl, fl, ba, fa = pose(name)
    hip_y = s["hip_y"] + bob
    sh_y = s["shoulder_y"] + bob
    cx = 16 + lean

    def leg_points(hip, ang):
        thigh, bend = ang
        knee = rot(hip, thigh, s["thigh"])
        foot = rot(knee, thigh - bend, s["shin"])
        return [hip, knee, foot]

    def arm_points(sh, ang):
        upper, bend = ang
        elbow = rot(sh, upper, s["upper"])
        hnd = rot(elbow, upper + bend, s["fore"])
        return [sh, elbow, hnd]

    idle = name.startswith("idle")
    pocket = s["hand_in_pocket"] and idle
    layers = []
    back_arm = arm_points((cx - 1.5, sh_y), ba)
    front_arm = arm_points((cx + 1.5, sh_y), fa)
    back_leg = leg_points((cx - 1.5, hip_y), bl)
    front_leg = leg_points((cx + 1.5, hip_y), fl)

    layers.append(limb(s["arm_r"], (s["sleeve"][2], s["sleeve"][2], 1), back_arm))
    if not pocket:
        layers.append(hand(back_arm[2]))

    leg_mid, leg_light, leg_dark = s["leg"]
    for pts, is_back in ((back_leg, True), (front_leg, False)):
        lc = limb(s["leg_r"], (leg_dark, None, 1) if is_back else (leg_mid, leg_light, leg_dark), pts)
        if not is_back and s["rip"] is not None:
            kx, ky = pts[1]
            lc.set(int(kx), int(ky), 14)
        layers.append(lc)
        layers.append(shoe(pts[2], s["shoe"]))

    torso = Canvas(32, 32)
    torso.blit(hero.torso, s["torso_x"] + lean, s["torso_y"] + bob)
    shade(torso, *s["torso_shade"])
    layers.append(torso)

    head = Canvas(32, 32)
    head_bob = bob + (1 if name == "land" else 0)
    head.blit(hero.head, s["head_x"] + lean, s["head_top"] + head_bob)
    layers.append(head)

    if pocket:
        layers.append(limb(s["arm_r"], s["sleeve"], front_arm))
    else:
        layers.append(limb(s["arm_r"], s["sleeve"], front_arm))
        hl = hand(front_arm[2])
        if name in SPOON:
            draw_spoon(hl, front_arm[2], SPOON[name], s["steel"])
        layers.append(hl)

    out = Canvas(32, 32)
    for layer in layers:
        out.blit(outlined(layer, 1))
    # plant the feet on the bottom row (airborne frames keep their offset)
    low = max(y for y in range(32) for x in range(32) if out.px[y][x])
    if name not in ("jump", "apex", "fall", "hurt"):
        out = out.shifted(0, 31 - low)
    return out


def sheet(hero):
    big = Canvas(32, 32 * len(FRAMES))
    for i, n in enumerate(FRAMES):
        big.blit(frame(hero, n), 0, 32 * i)
    return big


def main():
    os.makedirs(OUT, exist_ok=True)
    for hero in (JON, WES):
        pal = [snes_color(c) for c in hero.pal]
        to_image(sheet(hero), pal).save(os.path.join(OUT, f"{hero.name}.png"))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
