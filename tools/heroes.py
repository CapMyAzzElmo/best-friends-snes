"""Generates Jon and Wes sprite sheets (32x64 frames, facing right).

Each frame is drawn from layered parts (limbs, torso, head) with per-part
outlines, so the front arm gets its own line where it crosses the body,
the way Mega Man X sprites read.

Output: art/sprites/<hero>.png, a 32 x (64 * frames) indexed PNG with a
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

FRAMES = ["idle0", "idle1", "run0", "run1", "run2", "run3", "run4", "run5",
          "jump", "fall", "throw0", "throw1", "hurt"]

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
    ".....oooooo.....",
    "...ooHHHhhHoo...",
    "..oHHHhhhhHHHo..",
    ".oHHHHHHHHHHHHo.",
    ".oHHHHHHHHHHHHHo",
    "oHHHHHHHHHHSHHSo",
    "oHHHHHHHHSSSSSSo",
    "oHHHHsSSSSSSSSSo",
    "oHHHsdsSSoSSSoSo",
    "oHHHsdsSSoSSSoSSo",
    ".oHHssSSSSSSSSdo",
    ".oHdssSSSSSoooSo",
    "..oddsSSSSowwwo.",
    "...oddsSSSSooo..",
    "....oooooooo....",
]
JON_HEAD_LEGEND = {"o": 1, "S": 2, "s": 3, "d": 4, "H": 5, "h": 6, "w": 14}

JON_TORSO = [  # hoodie, 14 wide; drawn with the neck at the top
    "..oHHHHHo.....",
    ".oHHHMMMMMo...",
    "oHHMMMMMMMMMo.",
    "oHMMMMMMMMMMMo",
    "oHMMMMMMtMtMMo",
    "oHMMMMMMtMtMMo",
    "oHMMMMMMMMMMMo",
    "oHMMMMMMMMMMMo",
    "oHMMMMpppppMMo",
    "oHMMMpMMMMMpMo",
    "oHMMMMMMMMMMMo",
    "oHHMMMMMMMMMMo",
    "oHHMMMMMMMMMMo",
    "oHHHHHHHHHHHHo",
    ".oooooooooooo.",
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
    "....oooooooo......",
    "..ooCCCCcccCoo....",
    ".oCCCCCCCCccCCo...",
    ".oCCCCCCCCCCCCCo..",
    "oCCCCCCCCCCCCCCooo",
    "oCCCCCCCCCCCCBBBBBo",
    "oCCCCCCCCBBBBBbbbbo",
    "oCCCsSSSSSSooooooo.",
    "oCCsdsSoLLLLoLLLo..",
    "oCCsdsSoLLLLoLLLo..",
    ".oCssSSSooooSoooSo.",
    ".oCdsSSSSSSSSSSSo..",
    "..odssSSgGGGGgGGo..",
    "..oddsSgGGooooGo...",
    "...oddgGGGGGGGo....",
    "....ooGGGGGGoo.....",
    "......oooooo.......",
]
WES_HEAD_LEGEND = {"o": 1, "S": 2, "s": 3, "d": 4, "G": 5, "g": 6, "C": 7, "c": 8,
                   "B": 10, "b": 11, "L": 14}

WES_TORSO = [  # charcoal button-up, open over a black tee
    "..oMMMMMMo....",
    ".oMMMMTTTMo...",
    "oMMMMMTTTTMo..",
    "oMMMMMMTTTTMo.",
    "oMMMMMMTTTTMo.",
    "oMMMMMMMTTTMo.",
    "oMMMMMMMTTTMo.",
    "oMMMMMMMTTTMo.",
    "oMMMMMMMTTTMo.",
    "oMMMMMMMTTTMo.",
    "oDDDDDDDDDDDo.",
    ".oooooooooooo.",
]
WES_TORSO_LEGEND = {"o": 1, "M": 8, "T": 7, "D": 13}


class Hero:
    def __init__(self, name, pal, head, head_legend, torso, torso_legend, spec):
        self.name, self.pal, self.spec = name, pal, spec
        self.head = ascii_canvas(head, head_legend)
        self.torso = ascii_canvas(torso, torso_legend)


JON = Hero("jon", JON_PAL, JON_HEAD, JON_HEAD_LEGEND, JON_TORSO, JON_TORSO_LEGEND, dict(
    head_top=15, head_x=9, torso_x=9, torso_y=29, hip_y=43, shoulder_y=33,
    thigh=9, shin=9, upper=7, fore=7, leg_r=2.6, arm_r=2.0,
    leg=(11, 12, 10), sleeve=(8, 9, 7), shoe=13, steel=15, rip=10,
    torso_shade=(8, 9, 7), hand_in_pocket=True))

WES = Hero("wes", WES_PAL, WES_HEAD, WES_HEAD_LEGEND, WES_TORSO, WES_TORSO_LEGEND, dict(
    head_top=20, head_x=7, torso_x=9, torso_y=35, hip_y=46, shoulder_y=38,
    thigh=8, shin=8, upper=6, fore=6, leg_r=3.0, arm_r=2.3,
    leg=(12, None, 13), sleeve=(8, 9, 7), shoe=15, steel=14, rip=None,
    torso_shade=(8, 9, 7), hand_in_pocket=False))


def limb(spec_r, color3, points):
    mid, light, dark = color3
    c = Canvas(32, 64)
    for a, b in zip(points, points[1:]):
        capsule(c, a, b, spec_r, mid)
    shade(c, mid, light if light is not None else mid, dark)
    return c


def hand(pos, r=1.6):
    c = Canvas(32, 64)
    ellipse(c, pos[0], pos[1], r, r, 3)
    shade(c, 3, 2, 4)
    return c


def shoe(foot, ang, color):
    c = Canvas(32, 64)
    tip = (foot[0] + 3.5, foot[1] + 0.2)
    capsule(c, (foot[0] - 1, foot[1]), tip, 1.8, color)
    return c


def pose(name):
    """Joint angles for each frame: (bob, back_leg, front_leg, back_arm, front_arm).

    Legs: (thigh angle, knee bend). Arms: (upper angle, elbow bend). Angles in degrees
    from straight down; positive swings toward the facing direction.
    """
    if name == "idle0":
        return 0, (-6, 4), (8, 4), (-6, 12), (6, 18)
    if name == "idle1":
        return 1, (-6, 6), (8, 6), (-4, 16), (8, 24)
    if name.startswith("run"):
        i = int(name[3:])
        ph = i / 6 * 2 * math.pi
        def leg(p):
            thigh = 38 * math.sin(p)
            bend = 18 + 62 * max(0.0, math.sin(p - math.pi / 2)) ** 1.2
            return thigh, bend
        bob = 1 if i in (1, 4) else 0
        return bob, leg(ph + math.pi), leg(ph), (-34 * math.sin(ph), 70), (34 * math.sin(ph), 70)
    if name == "jump":
        return -2, (-24, 40), (58, 95), (-60, 40), (70, 60)
    if name == "fall":
        return -1, (-14, 20), (30, 40), (-100, 30), (110, 30)
    if name == "throw0":   # spoon cocked back over the shoulder
        return 0, (-14, 6), (18, 10), (-10, 30), (-95, -60)
    if name == "throw1":   # fling forward
        return 1, (-22, 8), (24, 12), (-30, 20), (125, -25)
    if name == "hurt":
        return 0, (-20, 30), (14, 20), (-150, 20), (115, 30)
    raise ValueError(name)


def draw_spoon(c, hand_pos, ang, steel):
    """Big serving spoon held in the front hand; ang is direction of the handle."""
    a = math.radians(ang)
    dx, dy = math.sin(a), -math.cos(a)
    tip = (hand_pos[0] + dx * 8, hand_pos[1] + dy * 8)
    capsule(c, hand_pos, tip, 1.0, steel)
    ellipse(c, tip[0] + dx * 2, tip[1] + dy * 2, 2.8, 2.8, steel)
    ellipse(c, tip[0] + dx * 1.6 - 0.8, tip[1] + dy * 1.6 - 0.8, 1.0, 1.0, 14)


def frame(hero, name):
    s = hero.spec
    bob, bl, fl, ba, fa = pose(name)
    hip_y = s["hip_y"] + bob
    sh_y = s["shoulder_y"] + bob
    cx = 16

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

    layers = []
    back_arm = arm_points((cx - 2, sh_y), ba)
    front_arm = arm_points((cx + 1, sh_y), fa)
    back_leg = leg_points((cx - 2, hip_y), bl)
    front_leg = leg_points((cx + 2, hip_y), fl)

    dark_sleeve = (s["sleeve"][2], s["sleeve"][2], 1)
    layers.append(limb(s["arm_r"], dark_sleeve, back_arm))
    if not (s["hand_in_pocket"] and name.startswith("idle")):
        layers.append(hand(back_arm[2]))

    leg_mid, leg_light, leg_dark = s["leg"]
    for pts, is_back in ((back_leg, True), (front_leg, False)):
        lc = limb(s["leg_r"], (leg_dark, None, 1) if is_back else (leg_mid, leg_light, leg_dark), pts)
        if not is_back and s["rip"] is not None:
            kx, ky = pts[1]
            lc.set(int(kx) + 1, int(ky), 14)
            lc.set(int(kx), int(ky), s["rip"])
        layers.append(lc)
        layers.append(shoe(pts[2], 0, s["shoe"]))

    torso = Canvas(32, 64)
    torso.blit(hero.torso, s["torso_x"], s["torso_y"] + bob)
    shade(torso, *s["torso_shade"])
    layers.append(torso)

    head = Canvas(32, 64)
    head.blit(hero.head, s["head_x"], s["head_top"] + bob)
    arm_behind_head = False
    if not arm_behind_head:
        layers.append(head)

    if s["hand_in_pocket"] and name.startswith("idle"):
        layers.append(limb(s["arm_r"], s["sleeve"], front_arm))
    else:
        arm = limb(s["arm_r"], s["sleeve"], front_arm)
        layers.append(arm)
        hl = hand(front_arm[2])
        if name.startswith("throw"):
            spoon_ang = {"throw0": -40, "throw1": 15}[name]
            draw_spoon(hl, front_arm[2], spoon_ang, s["steel"])
        layers.append(hl)
    if arm_behind_head:
        layers.append(head)

    out = Canvas(32, 64)
    for layer in layers:
        out.blit(outlined(layer, 1))
    # feet planted: shift whole frame so the lowest pixel sits on row 63
    low = max(y for y in range(64) for x in range(32) if out.px[y][x])
    if name not in ("jump", "fall", "hurt"):
        out = out.shifted(0, 63 - low)
    return out


def sheet(hero):
    big = Canvas(32, 64 * len(FRAMES))
    for i, n in enumerate(FRAMES):
        big.blit(frame(hero, n), 0, 64 * i)
    return big


def main():
    os.makedirs(OUT, exist_ok=True)
    for hero in (JON, WES):
        pal = [snes_color(c) for c in hero.pal]
        img = to_image(sheet(hero), pal)
        img.save(os.path.join(OUT, f"{hero.name}.png"))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
