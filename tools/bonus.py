"""Art for the two bonus rounds.

Road Ride: Jon's black Suzuki B-King and Wes's red Honda RC51 racing down a
coastal highway, dodging cones, oil slicks and traffic.
The Range: a sunny outdoor shooting range with steel plates, bottles and
clay pigeons.

Writes (build/):
  race_bg1.pic/.map  road layer (64x32 map, repeats every 512px)
  race_bg2.pic/.map  sky, sea and hills
  race_bg.pal        BG palettes
  race_big.pic       32x32: jon bike ride0/ride1/boost/crash halves (0-7),
                     wes bike (8-15), car ride0/ride1 halves (16-19),
                     oil slick 20, boost pad 21, finish flag 22
  race_small.pic     16x16: cone 0, cone hit 1, spark 2-4, dust 5-6
  jonbike.pal, wesbike.pal, bonus_obj.pal (sprite palettes 3, 4, 7)
  range_bg1.pic/.map, range_bg2.pic/.map, range_bg.pal
  range_big.pic      32x32: plate up 0, plate hit 1, plate down 2
  range_small.pic    16x16: crosshair 0-1, bottle 2, bottle shatter 3,
                     clay 4-5, clay shatter 6, spark 7-9, flash 10
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, capsule, ellipse, shade, outlined, to_image, snes_color
from snesgfx import tile_4bpp, palette_bytes, words
from sprites_build import grid_pic
from stagekit import noise, fill, frame_box
import critters

ROOT = os.path.join(os.path.dirname(__file__), "..")
BUILD = os.path.join(ROOT, "build")
SPR = os.path.join(ROOT, "art", "sprites")
ART = os.path.join(ROOT, "art", "bg")
MAGENTA, OUT = (255, 0, 255), (20, 16, 28)

JON_BIKE = [MAGENTA, OUT,
            (30, 30, 36), (180, 184, 196), (240, 240, 250),       # 2 tyre, 3 silver, 4 chrome
            (40, 40, 52), (72, 74, 92), (116, 120, 142),          # 5-7 B-King black paint
            (96, 96, 108), (150, 150, 162),                       # 8 engine, 9 exhaust
            (28, 28, 38), (56, 56, 72),                           # 10-11 hoodie
            (176, 200, 224), (120, 148, 184),                     # 12-13 light jeans
            (90, 140, 200), (250, 230, 150)]                      # 14 visor, 15 headlight
WES_BIKE = [MAGENTA, OUT,
            (30, 30, 36), (180, 184, 196), (240, 240, 250),
            (200, 40, 44), (244, 96, 84), (130, 24, 32),          # 5-7 RC51 red
            (96, 96, 108), (150, 150, 162),
            (76, 78, 90), (108, 112, 126),                        # 10-11 charcoal shirt
            (60, 68, 100), (38, 44, 70),                          # 12-13 dark pants
            (148, 204, 244), (250, 230, 150)]                     # 14 sky-blue visor, 15 light
OBJ_PAL = [MAGENTA, OUT,
           (250, 130, 40), (200, 80, 20),                         # 2-3 cone orange
           (248, 248, 240),                                       # 4 white
           (60, 110, 200), (100, 150, 240), (36, 70, 140),        # 5-7 car blue
           (30, 30, 36), (180, 184, 196),                         # 8 tyre/black, 9 silver
           (40, 36, 50), (90, 70, 120),                           # 10 oil, 11 oil sheen
           (130, 230, 90), (250, 220, 70),                        # 12 boost green, 13 yellow
           (150, 160, 170), (224, 56, 56)]                        # 14 steel, 15 red


# ------------------------------------------------------------------ bikes
def bike(kind, frame):
    """64x32 side view, facing right. kind: 'jon' (B-King) or 'wes' (RC51)."""
    crash = frame == "crash"
    boost = frame == "boost"
    spin = 1 if frame == "ride1" else 0
    c = Canvas(64, 32)
    wheels = Canvas(64, 32)
    rear, front = (12, 25), (51, 25)
    if boost:
        front = (52, 20)                                  # wheelie
    for (wx, wy) in (rear, front):
        ellipse(wheels, wx, wy, 6.5, 6.5, 2)
        ellipse(wheels, wx, wy, 4, 4, 3)
        ellipse(wheels, wx, wy, 1.5, 1.5, 8)
        for k in range(3):                                # spokes
            a = math.radians(k * 120 + spin * 60)
            wheels.set(int(wx + math.cos(a) * 3), int(wy + math.sin(a) * 3), 8)
    frame_l = Canvas(64, 32)
    fx, fy = front
    capsule(frame_l, (fx, fy), (fx - 6, fy - 13), 1.0, 9)    # fork
    capsule(frame_l, rear, (28, 20), 1.2, 8)                  # swingarm
    body = Canvas(64, 32)
    lift = -5 if boost else 0
    if kind == "jon":
        # B-King: big muscular tank, exposed engine, stubby twin exhausts under the tail
        ellipse(body, 33, 13 + lift * 0.5, 10, 5, 5)         # tank
        ellipse(body, 22, 15 + lift * 0.3, 8, 3, 6)          # seat
        capsule(body, (15, 13 + lift * 0.2), (8, 11), 2, 5)   # tail
        fill(body, 26, 17, 40, 25, 8)                         # engine block
        for x in range(27, 40, 3):
            capsule(body, (x, 17), (x, 24), 0.4, 9)
        capsule(body, (19, 17), (7, 14), 1.3, 3)              # stacked twin mufflers
        capsule(body, (19, 20), (8, 18), 1.1, 3)
        body.set(7, 14, 4); body.set(8, 18, 4)
        ellipse(body, 46, 12 + lift * 0.7, 3, 3.5, 3)         # round headlight
        body.set(48, 12 + int(lift * 0.7), 15)
        shade(body, 5, 7, 5)
    else:
        # RC51: full red fairing, pointed nose, high side exhausts under the seat
        pts = [(10, 10), (24, 9), (40, 6), (50, 10), (52, 14), (44, 22), (28, 24), (18, 18)]
        for y in range(4, 26):
            for x in range(8, 56):
                inside = False
                j = len(pts) - 1
                for i in range(len(pts)):
                    (xi, yi), (xj, yj) = pts[i], pts[j]
                    yi2, yj2 = yi + lift * (xi / 56), yj + lift * (xj / 56)
                    if ((yi2 > y) != (yj2 > y)) and (x < (xj - xi) * (y - yi2) / (yj2 - yi2 + 1e-9) + xi):
                        inside = not inside
                    j = i
                if inside:
                    body.set(x, y, 5)
        for x in range(30, 46):                               # silver side panel stripe
            body.set(x, 16 + int(lift * x / 56), 3)
        capsule(body, (20, 16), (8, 12), 2, 9)                # high exhausts
        capsule(body, (46, 9 + lift * 0.8), (51, 11 + lift * 0.8), 1.2, 14)   # screen
        body.set(51, 13 + int(lift * 0.8), 15)
        shade(body, 5, 6, 7)
    rider = Canvas(64, 32)
    hip = (24, 11 + lift * 0.4)
    shoulder = (34, 4 + lift * 0.6)
    capsule(rider, hip, shoulder, 2.3, 10)                     # crouched torso
    capsule(rider, hip, (30, 16 + lift * 0.3), 1.8, 12)        # thigh
    capsule(rider, (30, 16 + lift * 0.3), (27, 21), 1.5, 13)   # shin to peg
    capsule(rider, shoulder, (42, 9 + lift * 0.7), 1.5, 11)    # arm to the bars
    helmet = (38, 2 + lift * 0.6)
    ellipse(rider, helmet[0], helmet[1], 4.2, 3.6, 5 if kind == "jon" else 4)
    capsule(rider, (helmet[0] + 1, helmet[1]), (helmet[0] + 4, helmet[1] + 1), 1, 14)
    if kind == "wes":
        ellipse(rider, helmet[0] - 1, helmet[1] - 1, 3, 1.5, 14)   # sky-blue stripe nod to the cap
    shade(rider, 10, 11, 10)
    out = Canvas(64, 32)
    for layer in (frame_l, wheels, body, rider):
        out.blit(outlined(layer, 1))
    if crash:
        # tumble: rotate the whole bike a quarter turn around its middle
        rot = Canvas(64, 32)
        for y in range(32):
            for x in range(64):
                sx = 32 + (x - 32) * 0.94 + (y - 20) * 0.34
                sy = 20 - (x - 32) * 0.34 + (y - 20) * 0.94
                v = out.get(int(sx), int(sy))
                if v:
                    rot.set(x, y, v)
        out = rot
    if boost:
        for (x, y) in ((1, 27), (3, 24), (0, 21)):              # exhaust flames
            out.set(x, y, 15); out.set(x + 1, y, 15)
    return out


def car(spin):
    c = Canvas(64, 32)
    body = Canvas(64, 32)
    fill(body, 4, 14, 60, 25, 5)
    for x in range(14, 46):                                     # cabin
        top = 4 + max(0, 6 - (x - 14)) + max(0, (x - 40))
        for y in range(top, 14):
            body.set(x, y, 5)
    fill(body, 18, 6, 29, 13, 9)                                 # windows
    fill(body, 31, 6, 41, 13, 9)
    shade(body, 5, 6, 7)
    body.set(59, 17, 13); body.set(4, 17, 15)
    wheels = Canvas(64, 32)
    for wx in (14, 50):
        ellipse(wheels, wx, 25, 5.5, 5.5, 8)
        ellipse(wheels, wx, 25, 2.5, 2.5, 9)
        wheels.set(wx + (1 if spin else -1), 25, 8)
    out = Canvas(64, 32)
    for layer in (body, wheels):
        out.blit(outlined(layer, 1))
    return out


def oil_slick():
    c = Canvas(32, 32)
    ellipse(c, 16, 26, 14, 4, 10)
    ellipse(c, 12, 25, 5, 1.5, 11)
    ellipse(c, 21, 27, 4, 1.2, 11)
    return c


def boost_pad():
    c = Canvas(32, 32)
    fill(c, 2, 20, 30, 31, 12)
    for k in range(3):
        x0 = 6 + k * 8
        for i in range(5):
            c.set(x0 + i, 22 + i, 13); c.set(x0 + i, 29 - i, 13)
    return outlined(c, 1)


def finish_flag():
    c = Canvas(32, 32)
    capsule(c, (4, 2), (4, 31), 0.8, 9)
    for y in range(2, 18):
        for x in range(5, 28):
            c.set(x, y, 4 if ((x - 5) // 4 + (y - 2) // 4) % 2 == 0 else 8)
    return outlined(c, 1)


def cone(hit):
    c = Canvas(16, 16)
    if not hit:
        for y in range(3, 14):
            half = (y - 3) * 0.45 + 0.6
            for x in range(int(8 - half), int(8 + half) + 1):
                c.set(x, y, 2 if (y // 3) % 2 == 0 else 4)
        fill(c, 2, 13, 15, 15, 3)
    else:
        for x in range(2, 13):
            half = (x - 2) * 0.35 + 0.6
            for y in range(int(11 - half), int(11 + half) + 1):
                c.set(x, y, 2 if (x // 3) % 2 == 0 else 4)
    return outlined(c, 1)


def dust(i):
    c = Canvas(16, 16)
    for (x, y, r) in ((6, 10, 3), (10, 9, 2.5), (8, 7, 2)) if i == 0 else ((5, 9, 2), (11, 8, 2), (8, 5, 1.5)):
        ellipse(c, x, y, r, r, 14)
    return c


# ------------------------------------------------------------------ road scene
P_ROAD = [(0, 0, 0), (20, 20, 28),
          (70, 72, 80), (54, 56, 64), (40, 42, 50),               # 2-4 asphalt
          (240, 240, 230), (230, 200, 70),                        # 5 white line, 6 yellow line
          (190, 190, 200), (130, 130, 140),                       # 7-8 guardrail
          (110, 180, 80), (76, 140, 60), (50, 100, 44),           # 9-11 verge grass
          (200, 180, 140), (160, 140, 100),                       # 12-13 gravel shoulder
          (230, 60, 50), (250, 250, 240)]                         # 14 red post, 15 white
P_COAST = [(0, 0, 0), (40, 50, 80),
           (150, 210, 250), (120, 190, 245), (96, 170, 236),      # 2-4 sky
           (250, 250, 255), (210, 230, 250),                      # 5-6 clouds
           (60, 130, 200), (40, 100, 170), (180, 230, 250),       # 7-9 sea
           (90, 150, 90), (60, 116, 70), (40, 84, 54),            # 10-12 hills
           (120, 110, 130), (90, 84, 104),                        # 13-14 far mountains
           (250, 240, 200)]                                       # 15 sun


def tilemap_export(c, pal_of, name, tile_limit=512):
    """c: canvas w x 224, pal_of(tx, ty) -> palette number. Writes .pic and a
    64x32 map (SC_64x32 layout, w must be 256 or 512)."""
    w = c.w
    tiles, tl = {}, []
    tmap = [[0] * 64 for _ in range(32)]
    for ty in range(28):
        for tx in range(64):
            sx = (tx * 8) % w
            px = tuple(tuple(c.px[ty * 8 + y][sx + x] for x in range(8)) for y in range(8))
            if px not in tiles:
                tiles[px] = len(tl)
                tl.append(px)
            tmap[ty][tx] = tiles[px] | (pal_of(tx % (w // 8), ty) << 10)
    assert len(tl) <= tile_limit, (name, len(tl))
    with open(os.path.join(BUILD, f"{name}.pic"), "wb") as f:
        for px in tl:
            f.write(tile_4bpp(px))
    data = []
    for screen in range(2):
        for y in range(32):
            for x in range(32):
                data.append(tmap[y][screen * 32 + x])
    with open(os.path.join(BUILD, f"{name}.map"), "wb") as f:
        f.write(words(data))
    print(f"{name}: {len(tl)} tiles")


def road_layer():
    W = 512
    c = Canvas(W, 224)
    # guardrail strip 104-119, verge 120-127, road 128-207, shoulder 208-223
    for x in range(W):
        for y in range(104, 120):
            if y in (106, 107, 112, 113):
                c.set(x, y, 7 if y % 2 == 0 else 8)
            elif x % 32 in (0, 1) and y >= 106:
                c.set(x, y, 14 if y < 110 else 8)
        for y in range(120, 128):
            c.set(x, y, 9 if y < 122 else (10 if noise(x % 64, y, 171) > 0.4 else 11))
        for y in range(128, 208):
            n = noise(x % 64, y, 173)
            c.set(x, y, 3 if n < 0.75 else (2 if n < 0.9 else 4))
        for y in (128, 129):
            c.set(x, y, 5)
        for y in (206, 207):
            c.set(x, y, 5)
        if x % 48 < 24:                                      # dashed lane lines
            for y in (155, 156, 181, 182):
                c.set(x, y, 5)
        for y in range(208, 224):
            c.set(x, y, 12 if noise(x % 64, y, 175) > 0.3 else 13)
    return c


def coast_layer():
    W = 512
    c = Canvas(W, 224)
    for y in range(224):
        col = 4 if y < 30 else (3 if y < 64 else 2)
        for x in range(W):
            c.set(x, y, col)
    ellipse(c, 420, 30, 10, 10, 15)
    for (cx, cy, s) in ((80, 24, 1.0), (260, 40, 0.7), (360, 18, 0.9)):
        for (dx, dy, r) in ((0, 0, 12), (14, 2, 10), (-13, 3, 9)):
            ellipse(c, cx + dx * s, cy + dy * s, r * s * 1.3, r * s * 0.6, 6)
        for (dx, dy, r) in ((0, -1, 10), (11, 0, 7)):
            ellipse(c, cx + dx * s, cy + dy * s - 2, r * s * 1.2, r * s * 0.5, 5)
    for x in range(W):                                         # mountains
        h = 22 + 14 * math.sin(x / 41) + 8 * math.sin(x / 17 + 1)
        for y in range(int(86 - h), 86):
            c.set(x, y, 13 if (y + x // 3) % 7 else 14)
    for y in range(86, 104):                                   # the sea
        for x in range(W):
            c.set(x, y, 7 if y < 94 else 8)
            if (x * 7 + y * 13) % 23 == 0:
                c.set(x, y, 9)
    for x in range(W):                                         # rolling hills in front
        h = 10 + 6 * math.sin(x / 23) + 3 * math.sin(x / 9)
        for y in range(int(104 - h), 224):
            c.set(x, y, 10 if y < 104 - h + 3 else 11)
    return c


# ------------------------------------------------------------------ range scene
P_RANGE = [(0, 0, 0), (34, 26, 24),
           (190, 140, 90), (150, 104, 64), (110, 74, 46),          # 2-4 bench wood
           (210, 180, 130), (176, 146, 100), (140, 112, 76),       # 5-7 dirt berm
           (100, 160, 70), (70, 120, 54),                          # 8-9 grass
           (150, 150, 160), (100, 100, 110),                       # 10-11 steel stands
           (250, 240, 220),                                        # 12 paper
           (220, 60, 50),                                          # 13 red
           (250, 200, 70), (60, 40, 30)]                           # 14 sign yellow, 15 dark
P_RANGE_SKY = [(0, 0, 0), (40, 50, 80),
               (160, 210, 250), (130, 194, 246), (104, 176, 238),
               (250, 250, 255), (214, 232, 250),
               (120, 150, 100), (90, 120, 80), (66, 92, 64),       # 7-9 tree line
               (180, 160, 140), (150, 130, 112),                   # 10-11 far hills
               (230, 210, 170), (200, 170, 130),                   # 12-13 berm far
               (250, 240, 200), (90, 70, 50)]


def range_front():
    W = 256
    c = Canvas(W, 224)
    # dirt berm 96-151 behind the targets, grass lane 152-175, shooting bench 176-223
    for y in range(96, 152):
        for x in range(W):
            top = 96 + int(4 * math.sin(x / 19))
            if y >= top:
                n = noise(x, y, 181)
                c.set(x, y, 6 if n < 0.6 else (5 if n < 0.85 else 7))
    for y in range(152, 176):
        for x in range(W):
            c.set(x, y, 8 if noise(x, y, 183) < 0.7 else 9)
    for x0 in (36, 116, 196):                                  # target stands (plates sit on them)
        fill(c, x0 - 1, 136, x0 + 1, 160, 11)
        fill(c, x0 - 8, 158, x0 + 8, 160, 10)
    for x in range(W):                                         # fence rail for bottles
        c.set(x, 120, 3); c.set(x, 121, 4)
    for x0 in range(8, W, 48):
        fill(c, x0, 120, x0 + 3, 152, 4)
    for y in range(176, 224):                                  # shooting bench
        for x in range(W):
            if y < 182:
                c.set(x, y, 2 if y < 178 else 3)
            else:
                c.set(x, y, 3 if (x // 16 + y // 8) % 2 else 4)
    for x in range(W):
        c.set(x, 176, 1); c.set(x, 182, 1)
    # a sign: RANGE in blocky letters is too wordy for 8x8, so a yellow board
    fill(c, 104, 186, 152, 202, 14)
    frame_box(c, 104, 186, 152, 202, 15)
    for k in range(5):
        fill(c, 110 + k * 8, 191, 115 + k * 8, 197, 15)
    return c


def range_back():
    W = 256
    c = Canvas(W, 224)
    for y in range(224):
        col = 4 if y < 30 else (3 if y < 64 else 2)
        for x in range(W):
            c.set(x, y, col)
    for (cx, cy) in ((60, 30), (190, 46)):
        for (dx, dy, r) in ((0, 0, 12), (14, 2, 10), (-13, 3, 9)):
            ellipse(c, cx + dx, cy + dy, r * 1.3, r * 0.6, 6)
        ellipse(c, cx, cy - 3, 12, 5, 5)
    for x in range(W):
        h = 18 + 8 * math.sin(x / 31)
        for y in range(int(90 - h), 224):
            c.set(x, y, 10 if y < 90 - h + 4 else 11)
    for x in range(W):
        h = 8 + 4 * math.sin(x / 7) + 3 * math.sin(x / 3)
        for y in range(int(100 - h), 224):
            c.set(x, y, 8 if y < 100 - h + 3 else 9)
    return c


def plate(state):
    c = Canvas(32, 32)
    if state == 2:                                              # knocked flat
        fill(c, 6, 26, 26, 29, 14)
        return outlined(c, 1)
    tilt = 4 if state == 1 else 0
    for y in range(4, 24):
        for x in range(6, 26):
            if (x - 16) ** 2 + (y - 14) ** 2 <= 100:
                c.set(x + (tilt if y < 14 else 0), y, 14)
    shade(c, 14, 4, 9)
    ellipse(c, 16 + (tilt // 2), 14, 3, 3, 15)
    return outlined(c, 1)


def crosshair(i):
    c = Canvas(16, 16)
    r = 6 if i == 0 else 5
    for a in range(0, 360, 6):
        c.set(int(8 + math.cos(math.radians(a)) * r), int(8 + math.sin(math.radians(a)) * r), 15)
    for k in range(2, 6):
        c.set(8, 8 - r - 1 + k, 4); c.set(8, 8 + r + 1 - k, 4)
        c.set(8 - r - 1 + k, 8, 4); c.set(8 + r + 1 - k, 8, 4)
    c.set(8, 8, 15)
    return c


def bottle(broken):
    c = Canvas(16, 16)
    if not broken:
        fill(c, 6, 6, 10, 15, 12)
        fill(c, 7, 2, 9, 6, 12)
        c.set(7, 7, 4)
    else:
        for (x, y) in ((4, 12), (6, 13), (9, 12), (11, 14), (7, 10), (10, 9)):
            c.set(x, y, 12)
    return outlined(c, 1)


def clay(i):
    c = Canvas(16, 16)
    if i < 2:
        ellipse(c, 8, 8, 5, 2 if i == 0 else 3, 2)
        ellipse(c, 8, 7, 3, 1, 3)
    else:
        for (x, y) in ((3, 6), (6, 9), (11, 5), (12, 10), (8, 12)):
            c.set(x, y, 2); c.set(x + 1, y, 3)
    return outlined(c, 1)


def flash_puff():
    c = Canvas(16, 16)
    for a in range(8):
        ang = a * math.pi / 4
        capsule(c, (8, 8), (8 + math.cos(ang) * 6, 8 + math.sin(ang) * 6), 0.8, 13)
    ellipse(c, 8, 8, 2.5, 2.5, 4)
    return c


def stack(frames, size):
    sheet = Canvas(size, size * len(frames))
    for k, f in enumerate(frames):
        sheet.blit(f, 0, size * k)
    return sheet


def halves(c64):
    return [[[c64.px[y][h * 32 + x] for x in range(32)] for y in range(32)] for h in range(2)]


def main():
    os.makedirs(BUILD, exist_ok=True)
    # race sprites
    big = []
    previews = []
    for kind in ("jon", "wes"):
        for f in ("ride0", "ride1", "boost", "crash"):
            b = bike(kind, f)
            previews.append((kind, b))
            big += halves(b)
    for s in (0, 1):
        big += halves(car(s))
    big += [oil_slick().px, boost_pad().px, finish_flag().px]
    open(os.path.join(BUILD, "race_big.pic"), "wb").write(grid_pic(big, 32))
    small = [cone(0), cone(1), critters.spark(0), critters.spark(1), critters.spark(2), dust(0), dust(1)]
    open(os.path.join(BUILD, "race_small.pic"), "wb").write(grid_pic([s.px for s in small], 16))
    for name, p in (("jonbike", JON_BIKE), ("wesbike", WES_BIKE), ("bonus_obj", OBJ_PAL)):
        open(os.path.join(BUILD, f"{name}.pal"), "wb").write(palette_bytes([snes_color(c) for c in p]))
    to_image(stack([b for k, b in previews if k == "jon"], 32 if False else 64) if False else
             stack_64([b for k, b in previews if k == "jon"]), [snes_color(c) for c in JON_BIKE]).save(
        os.path.join(SPR, "jon_bike.png"))
    to_image(stack_64([b for k, b in previews if k == "wes"]), [snes_color(c) for c in WES_BIKE]).save(
        os.path.join(SPR, "wes_bike.png"))
    to_image(stack_64([car(0), car(1)]), [snes_color(c) for c in OBJ_PAL]).save(os.path.join(SPR, "race_car.png"))

    # race backgrounds: road in palette 1, coast in palette 2
    road = road_layer()
    tilemap_export(road, lambda tx, ty: 1, "race_bg1")
    coast = coast_layer()
    tilemap_export(coast, lambda tx, ty: 2, "race_bg2")
    pals = [[(0, 0, 0)] * 16 for _ in range(8)]
    pals[0][0] = P_COAST[4]
    pals[1], pals[2] = P_ROAD, P_COAST
    with open(os.path.join(BUILD, "race_bg.pal"), "wb") as f:
        for p in pals:
            f.write(palette_bytes([snes_color(c) for c in p]))

    # night and sunset versions of the road for the later races
    def tint(pal, mul, add, keep=()):
        return [c if i in keep or i == 0 else tuple(max(0, min(255, int(v * m + a))) for v, m, a in zip(c, mul, add))
                for i, c in enumerate(pal)]

    def write_pals(name, p0, p1, p2):
        pals = [[(0, 0, 0)] * 16 for _ in range(8)]
        pals[0][0] = p2[4]
        pals[1], pals[2] = p1, p2
        with open(os.path.join(BUILD, name), "wb") as f:
            for p in pals:
                f.write(palette_bytes([snes_color(c) for c in p]))

    road_n = tint(P_ROAD, (0.45, 0.45, 0.6), (0, 0, 10), keep=(5, 6, 14, 15))
    coast_n = tint(P_COAST, (0.3, 0.3, 0.45), (4, 6, 30))
    coast_n[2:5] = [(16, 20, 54), (22, 28, 70), (30, 38, 88)]
    coast_n[5:7] = [(70, 76, 110), (50, 56, 90)]
    coast_n[15] = (240, 240, 210)
    write_pals("race_bg_night.pal", None, road_n, coast_n)
    road_d = tint(P_ROAD, (1.0, 0.82, 0.7), (20, 0, 0), keep=(5, 6))
    coast_d = tint(P_COAST, (1.0, 0.75, 0.65), (30, 0, 10))
    coast_d[2:5] = [(250, 170, 100), (240, 130, 90), (210, 100, 100)]
    coast_d[5:7] = [(255, 220, 170), (250, 190, 140)]
    coast_d[15] = (255, 230, 120)
    write_pals("race_bg_dusk.pal", None, road_d, coast_d)

    # range
    front = range_front()
    tilemap_export(front, lambda tx, ty: 1, "range_bg1")
    back = range_back()
    tilemap_export(back, lambda tx, ty: 2, "range_bg2")
    pals = [[(0, 0, 0)] * 16 for _ in range(8)]
    pals[0][0] = P_RANGE_SKY[4]
    pals[1], pals[2] = P_RANGE, P_RANGE_SKY
    with open(os.path.join(BUILD, "range_bg.pal"), "wb") as f:
        for p in pals:
            f.write(palette_bytes([snes_color(c) for c in p]))
    rng_d = tint(P_RANGE, (0.8, 0.62, 0.62), (24, 4, 10), keep=(12, 13))
    sky_d = tint(P_RANGE_SKY, (0.9, 0.6, 0.6), (30, 0, 20))
    sky_d[2:5] = [(250, 160, 110), (230, 120, 100), (180, 90, 110)]
    sky_d[5:7] = [(255, 210, 170), (240, 180, 150)]
    write_pals("range_bg_dusk.pal", None, rng_d, sky_d)
    rbig = [plate(0).px, plate(1).px, plate(2).px]
    open(os.path.join(BUILD, "range_big.pic"), "wb").write(grid_pic(rbig, 32))
    rsmall = [crosshair(0), crosshair(1), bottle(False), bottle(True), clay(0), clay(1), clay(2),
              critters.spark(0), critters.spark(1), critters.spark(2), flash_puff()]
    open(os.path.join(BUILD, "range_small.pic"), "wb").write(grid_pic([s.px for s in rsmall], 16))
    to_image(stack(rsmall, 16), [snes_color(c) for c in OBJ_PAL]).save(os.path.join(SPR, "range_small.png"))

    # previews
    from PIL import Image
    img = Image.new("RGB", (512, 448))
    for name, cv, pal in (("road", road, P_ROAD), ("coast", coast, P_COAST)):
        pass
    snap = lambda rgb: tuple((v >> 3) << 3 for v in rgb)
    pix = img.load()
    for y in range(224):
        for x in range(512):
            v = road.px[y][x]
            pix[x, y] = snap(P_ROAD[v]) if v else snap(P_COAST[coast.px[y][x]] if coast.px[y][x] else P_COAST[4])
            if y < 224:
                v2 = front.px[y][x % 256]
                b2 = back.px[y][x % 256]
                pix[x, 224 + y] = snap(P_RANGE[v2]) if v2 else snap(P_RANGE_SKY[b2] if b2 else P_RANGE_SKY[4])
    img.save(os.path.join(ART, "bonus_preview.png"))
    print("bonus art written")


def stack_64(frames):
    sheet = Canvas(64, 32 * len(frames))
    for k, f in enumerate(frames):
        sheet.blit(f, 0, 32 * k)
    return sheet


if __name__ == "__main__":
    main()
