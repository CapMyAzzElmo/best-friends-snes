/*---------------------------------------------------------------------------------

    COMRADES - the platforming stages

    Hero, foes, weapons, breakable props and their pickups, checkpoints,
    lives, score, the HUD and the pause menu.

    Speed matters here: the 65816 C compiler turns every global array access
    into a dozen instructions, so the per-frame loops copy what they need
    into locals, only run foes near the camera, and avoid multiply, divide
    and modulo.

---------------------------------------------------------------------------------*/
#include "game.h"

extern char font_pic, font_pic_end, ui_pal;
extern char jon_pic, jon_pal, wes_pic, wes_pal, items_pic, items_pal;

// small sheet frames (see tools/foes.py)
#define SF_SHOT 0
#define SF_SPARK 2
#define SF_HEART 5
#define SF_C 6
#define SF_C_ALT 8
#define SF_C_HURT 10

// foe kinds and behaviours
#define KIND_A 1
#define KIND_B 2
#define KIND_C 3
#define B_WALK 0      // patrols
#define B_CHARGE 1    // lowers its head and rushes a hero in front of it
#define B_HOP 2       // hops in place
#define B_FLY 3       // bobs in the air and swoops down
#define B_SHOOT 4     // stops and throws at the hero
#define B_POUNCE 5    // crouches and leaps at the hero
#define B_ZIG 6       // weaves through the air after the hero
#define B_SCURRY 7    // darts fast, stops, darts again
#define B_GUARD 8     // faces the hero and blocks shots from the front
#define B_DROP 9      // flies high and drops things on the hero
#define B_BOUNCE 10   // bounces non-stop, steering at the hero
#define B_CHASE 11    // chases the hero down

#define MAX_FOES 24
#define MAX_ACTIVE 10
#define MAX_SHOTS 8
#define CHARGE_FULL 40    // frames of holding Y for a charged shot
#define MAX_SPARKS 6
#define MAX_PROPS 16
#define MAX_DROPS 4
#define WATER_Y 206           // feet below this: the hero is in a hazard
#define LOOK_AHEAD 44

// shot kinds
#define SK_LOB 0
#define SK_BOLT 1
#define SK_RANG 2
#define SK_BOMB 3
#define SK_BOOM 4

// per stage, per kind (A, B, C): behaviour, hit points, move mask, charge speed
const u8 foe_beh[18] = {
    B_CHARGE, B_WALK, B_HOP,        // goat, pig, chicken
    B_POUNCE, B_SHOOT, B_ZIG,       // cat, walking amp (sound waves), sour note
    B_CHARGE, B_SHOOT, B_SCURRY,    // punk, frat bro (bottles), rat
    B_GUARD, B_POUNCE, B_DROP,      // security, hot dog mascot, pigeon
    B_CHARGE, B_GUARD, B_FLY,       // floor buffer, suit of armour, bat
    B_CHARGE, B_CHASE, B_BOUNCE};   // golf cart, goose, bingo ball
const u8 foe_hp[18] = {2, 4, 1, 2, 4, 1, 2, 3, 1, 3, 3, 1, 3, 4, 1, 3, 2, 1};
// walk speed: the foe steps on frames where (frame & mask) == 0
const u8 foe_mask[18] = {1, 3, 0, 0, 3, 0, 1, 1, 0, 1, 3, 0, 0, 3, 0, 0, 1, 0};
const u8 foe_rush[18] = {2, 1, 0, 3, 0, 0, 2, 0, 0, 2, 0, 0, 3, 0, 0, 3, 2, 0};
// points (in tens) for each kind
const u8 foe_pts[4] = {0, 20, 30, 10};
// body box per kind: left, right, height
const u8 foe_x0[4] = {0, 5, 5, 3};
const u8 foe_x1[4] = {0, 27, 27, 13};
const u8 foe_h[4] = {0, 22, 22, 12};

// gentle bob for flyers
const s8 bobtab[16] = {0, 2, 4, 5, 6, 5, 4, 2, 0, -2, -4, -5, -6, -5, -4, -2};

char *const stagehud[6] = {"1 FFA", "2 JAM", "3 BAR TOWN", "4 CHICAGO", "5 COURT", "6 GOLDEN"};
char *const weapon_name[5] = {"      ", "SPREAD", "RAPID ", "PICK  ", "BOMBS "};

u16 i, j;

// ---------------------------------------------------------------- hero
u16 heroid;
t_objs *heroobj;
u16 *heroox, *herooy;
s16 *heroxv, *heroyv;
u16 herox, heroy;
u8 heroflip, heroframe;
u8 herohp, heroinvuln, herothrow, heroground, herowasground, herodead;
u8 coyote, jumpbuf, jumpcut, landtimer, stompchain, firehold;
u16 heroanim, runphase;
s16 hero_accel, hero_maxspeed, hero_jump, fallspeed;
s16 look;
u8 heroyofs, herotop;    // top of the hitbox below heroy: for the map, and for foes (lower when crouching)
u8 herocrouch, herocharge, chargeshot;
u8 stagedone;
u8 checkpoint;            // 0 stage start, 1-2 flags, 3 the arena gate
u8 lasthp, lastlives, lastweapon, cptimer;
u16 lastscore;

// shots use 1/16 pixel fixed point. One struct per shot, walked with a
// pointer: much cheaper for this compiler than a set of parallel arrays.
typedef struct
{
    u16 x;
    s16 y, vx, vy;
    u8 alive, life, kind, event;
    u8 power, spare;    // power: a charged shot (pierces, hits harder)
} Shot;
Shot shots[MAX_SHOTS];
u8 nshots;
s16 shbx0, shbx1, shby0, shby1;    // box around every live shot, for a quick miss
// scratch for shotsMove in fast.asm
s16 shpx, shpy, shvxl, shvyl, shhx, shhy;
u8 shkindl, shlifel, shevents;
void shotsMove(void);
u16 spx[MAX_SPARKS], spy[MAX_SPARKS];
u8 sptime[MAX_SPARKS];
u8 nsparks, ndrops, prfirst, prend;

// foes
u16 fx[MAX_FOES], fy[MAX_FOES], fmin[MAX_FOES], fmax[MAX_FOES];
u8 fkind[MAX_FOES], ft[MAX_FOES], fdir[MAX_FOES], fstate[MAX_FOES], fhp[MAX_FOES], ftimer[MAX_FOES];
u8 fframe[MAX_FOES];
s16 fhop[MAX_FOES], fhopv[MAX_FOES];
u8 nfoes, nact, kills;
u8 actlist[MAX_ACTIVE];
u8 refoes;    // set to rebuild the active list next frame
u8 ffirst;    // first foe that can be near the camera
#define FOE_WALK 0
#define FOE_CHARGE 1
#define FOE_HURT 2
#define FOE_DEAD 3

// breakable props: their state survives a respawn so the pickups can't be farmed
u16 prx[MAX_PROPS], pry[MAX_PROPS];
u8 pritem[MAX_PROPS], prstate[MAX_PROPS], prshake[MAX_PROPS];
u8 nprops;
#define PR_WHOLE 0
#define PR_CRACKED 1
#define PR_GONE 2

// pickups popped out of props (and the odd foe)
u16 drx[MAX_DROPS];
s16 dry[MAX_DROPS], drvy[MAX_DROPS], drfloor[MAX_DROPS];
u8 dritem[MAX_DROPS], dralive[MAX_DROPS];
u16 drtime[MAX_DROPS];

u16 cpx[2], cpy[2];
u8 heartgot[6];

// ---------------------------------------------------------------- HUD
void hudHearts(void)
{
    u8 k;
    for (k = 0; k < 5; k++)
    {
        if (k < hpmax[hero])
            hud[1 * 32 + 5 + k] = (k < herohp ? 0x40 : 0x41) | 0x2000 | (1 << 10);
        else
            hud[1 * 32 + 5 + k] = 0;
    }
    huddirty = 1;
    lasthp = herohp;
}

void hudLives(void)
{
    hud[1 * 32 + 11] = 0x44 | 0x2000 | (2 << 10);
    hudText(12, 1, "X");
    hudNumber(13, 1, lives, 2);
    if (lives < 10)
        hud[1 * 32 + 13] = 0;
    lastlives = lives;
}

void hudWeapon(void)
{
    hudTextPal(1, 2, weapon_name[weapon], 2);
    lastweapon = weapon;
}

void hudAll(void)
{
    hudClear();
    hudTextPal(1, 1, hero == HERO_JON ? "JON" : "WES", 2);
    hudHearts();
    hudLives();
    hudScore();
    hudWeapon();
    hudText(30 - slen(stagehud[stage]), 2, stagehud[stage]);
}

// ---------------------------------------------------------------- effects
void spawnSpark(u16 x, u16 y)
{
    for (j = 0; j < MAX_SPARKS; j++)
    {
        if (sptime[j] == 0)
        {
            spx[j] = x;
            spy[j] = y;
            sptime[j] = 12;
            nsparks++;
            return;
        }
    }
}

void spawnDrop(u16 x, s16 floor, u8 item)
{
    u8 k;
    for (k = 0; k < MAX_DROPS; k++)
    {
        if (!dralive[k])
        {
            dralive[k] = 1;
            ndrops++;
            drx[k] = x;
            dry[k] = (floor - 16) << 4;
            drvy[k] = -0x38;
            drfloor[k] = floor;
            dritem[k] = item;
            drtime[k] = 0;
            return;
        }
    }
}

// ---------------------------------------------------------------- weapons
void shotNew(u8 kind, s16 vx, s16 vy)
{
    Shot *p = shots;
    u8 k;
    for (k = 0; k < MAX_SHOTS; k++, p++)
    {
        if (!p->alive)
        {
            p->alive = 1;
            p->kind = kind;
            p->power = chargeshot;
            p->life = kind == SK_RANG ? 100 : 70;
            if (heroflip)
            {
                p->x = (herox + 6) << 4;
                vx = -vx;
            }
            else
                p->x = (herox + 26) << 4;
            if (kind != SK_RANG)
                vx += (*heroxv) >> 5;
            p->vx = vx;
            p->y = (heroy + (herocrouch ? 21 : 12)) << 4;
            p->vy = vy;
            nshots++;
            return;
        }
    }
}

u8 rangOut(void)
{
    Shot *p = shots;
    u8 k;
    for (k = 0; k < MAX_SHOTS; k++, p++)
        if (p->alive && p->kind == SK_RANG)
            return 1;
    return 0;
}

// the charged versions of each weapon
void fireCharged(void)
{
    chargeshot = 1;
    switch (weapon)
    {
    case W_SPREAD:
        shotNew(SK_LOB, 50, -56);
        shotNew(SK_LOB, 56, -40);
        shotNew(SK_LOB, 60, -24);
        shotNew(SK_LOB, 60, -8);
        shotNew(SK_LOB, 56, 6);
        break;
    case W_RAPID:
        shotNew(SK_BOLT, 104, -10);
        shotNew(SK_BOLT, 112, 0);
        shotNew(SK_BOLT, 104, 10);
        break;
    case W_RANG:
        shotNew(SK_RANG, 120, 0);
        break;
    case W_BOMB:
        shotNew(SK_BOMB, 52, -56);
        break;
    default:
        shotNew(SK_LOB, 62, -16);
        shotNew(SK_LOB, 60, -32);
        shotNew(SK_LOB, 56, -48);
        break;
    }
    chargeshot = 0;
    sfx(SFX_BOOST);
}

void fireWeapon(void)
{
    switch (weapon)
    {
    case W_SPREAD:
        shotNew(SK_LOB, 54, -46);
        shotNew(SK_LOB, 60, -24);
        shotNew(SK_LOB, 58, -4);
        break;
    case W_RAPID:
        shotNew(SK_BOLT, 88, 0);
        break;
    case W_RANG:
        shotNew(SK_RANG, 104, 0);
        break;
    case W_BOMB:
        shotNew(SK_BOMB, 46, -50);
        break;
    default:
        shotNew(SK_LOB, 56, -26);
        if (dblshot[hero])
            shotNew(SK_LOB, 48, -46);    // the Range prize adds a high lob
        break;
    }
    sfx(weapon == W_RAPID ? SFX_BANG : SFX_THROW);
}

void explode(Shot *p)
{
    p->kind = SK_BOOM;
    p->life = p->power ? 30 : 20;
    p->vx = 0;
    p->vy = 0;
    sfx(SFX_CRASH);
}

// returns the damage of a hero shot overlapping the box. Grapes and bolts
// burst on contact, bombs blow up, the pick flies on through.
u8 shotHits(u16 x0, u16 y0, u16 x1, u16 y1)
{
    Shot *p;
    u16 px, py, r;
    u8 n, kind, dmg;
    if (!nshots || (s16)x1 < shbx0 || (s16)x0 > shbx1 || (s16)y1 < shby0 || (s16)y0 > shby1)
        return 0;
    p = shots;
    for (n = 0; n < MAX_SHOTS; n++, p++)
    {
        if (!p->alive)
            continue;
        kind = p->kind;
        px = p->x >> 4;
        py = (u16)(p->y >> 4);
        r = (kind == SK_BOOM) ? (p->power ? 34 : 22) : ((kind == SK_RANG) ? 7 : (p->power ? 6 : 3));
        if (px + r > x0 && px < x1 + r && py + r > y0 && py < y1 + r)
        {
            dmg = p->power ? 3 : 1;
            if ((kind == SK_LOB || kind == SK_BOLT) && !p->power)
            {
                p->alive = 0;
                nshots--;
                spawnSpark(px - 8, py - 8);
                sfx(SFX_SPLAT);
            }
            else if (kind == SK_BOMB)
            {
                explode(p);
                dmg = p->power ? 5 : 3;
            }
            else if (kind == SK_BOOM)
                dmg = p->power ? 5 : 3;
            else if (kind == SK_RANG)
                dmg = p->power ? 4 : 2;
            return hero == HERO_WES ? dmg + 1 : dmg;    // Wes hits harder
        }
    }
    return 0;
}

void shotsUpdate(void)
{
    Shot *p;
    u8 n;
    if (!nshots)
        return;
    shotsMove();
    if (!shevents)
        return;
    p = shots;
    for (n = 0; n < MAX_SHOTS; n++, p++)
    {
        if (p->event == 1)
        {
            spawnSpark((p->x >> 4) - 8, 178);    // grapes splat on the floor
            sfx(SFX_SPLAT);
        }
        else if (p->event == 2)
            sfx(SFX_CRASH);
    }
}

// ---------------------------------------------------------------- hero
void heroinit(u16 xp, u16 yp, u16 type, u16 minx, u16 maxx)
{
    if (objNew(type, xp, yp) == 0)
        return;
    objGetPointer(objgetid);
    heroid = objgetid;
    heroobj = &objbuffers[objptr - 1];
    heroobj->xofs = 10;
    heroobj->width = 12;
    heroobj->yofs = heroyofs;
    heroobj->height = 31 - heroyofs;
    heroox = (u16 *)&(heroobj->xpos + 1);
    herooy = (u16 *)&(heroobj->ypos + 1);
    heroxv = (s16 *)&(heroobj->xvel);
    heroyv = (s16 *)&(heroobj->yvel);
    heroobj->action = ACT_STAND;
}

void heroHurt(s16 fromx)
{
    if (heroinvuln || herohp == 0 || stagedone)
        return;
    herohp--;
    heroinvuln = 90;
    herothrow = 0;
    *heroyv = -0x0300;
    if (fromx > (s16)herox + 16)
        *heroxv = -0x0180;
    else
        *heroxv = 0x0180;
    sfx(SFX_HURT);
}

void heroBounce(s16 vy)
{
    *heroyv = vy;
    jumpcut = 1;
    coyote = 0;
}

void heroupdate(u8 idx)
{
    s16 speed;
    heroobj = &objbuffers[idx];
    pad0 = padsCurrent(0);
    padpressed = padsDown(0);

    if (stagedone || herohp == 0)
        pad0 = 0, padpressed = 0;

    // jump buffering: a press shortly before landing still counts
    if (padpressed & KEY_B)
        jumpbuf = 6;
    else if (jumpbuf)
        jumpbuf--;

    // Down on the ground crouches: lower, so high shots and swoops pass over
    herocrouch = heroground && (pad0 & KEY_DOWN) && heroinvuln < 70;
    herotop = herocrouch ? heroyofs + 11 : heroyofs;

    if (heroinvuln < 70)    // brief loss of control after a hit
    {
        if (herocrouch)
        {
            // no walking while crouched, but you can turn to face
            *heroxv -= *heroxv >> 2;
            if (pad0 & KEY_LEFT)
                heroflip = 1;
            else if (pad0 & KEY_RIGHT)
                heroflip = 0;
        }
        else if (pad0 & KEY_LEFT)
        {
            heroflip = 1;
            // turning around is snappier than speeding up
            *heroxv -= (*heroxv > 0) ? hero_accel * 2 : hero_accel;
            if (*heroxv < -hero_maxspeed)
                *heroxv = -hero_maxspeed;
        }
        else if (pad0 & KEY_RIGHT)
        {
            heroflip = 0;
            *heroxv += (*heroxv < 0) ? hero_accel * 2 : hero_accel;
            if (*heroxv > hero_maxspeed)
                *heroxv = hero_maxspeed;
        }
        // coyote time: a few frames after running off a ledge you can still jump
        if (jumpbuf && coyote)
        {
            *heroyv = -hero_jump;
            jumpbuf = 0;
            coyote = 0;
            jumpcut = 0;
            sfx(SFX_JUMP);
        }
        // holding Y charges a shot, and letting go fires it
        if (pad0 & KEY_Y)
        {
            if (herocharge < 255)
                herocharge++;
            if (herocharge == CHARGE_FULL)
                sfx(SFX_POWERUP);
        }
        else
        {
            if (herocharge >= CHARGE_FULL && (weapon != W_RANG || rangOut() == 0))
            {
                fireCharged();
                herothrow = 6;    // past the point where the throw fires a normal shot
            }
            herocharge = 0;
        }
        // Y throws; the rapid fire keeps going while Y is held
        if (herothrow == 0)
        {
            if ((padpressed & KEY_Y) || (weapon == W_RAPID && (pad0 & KEY_Y)))
            {
                // (spelled out: the compiler gets "a || !f()" backwards)
                if (weapon == W_RAPID)
                    herothrow = 9;
                else if (weapon != W_RANG)
                    herothrow = 16;
                else if (rangOut() == 0)
                    herothrow = 16;    // one pick out at a time
            }
        }
    }
    // variable height: letting go of B early cuts the rise short
    if (!(pad0 & KEY_B) && !jumpcut && *heroyv < -0x0140)
    {
        *heroyv = -0x0140;
        jumpcut = 1;
    }
    // heavier fall than rise, with a terminal speed
    if (!heroground && *heroyv > -0x0080)
    {
        *heroyv += 22;
        if (*heroyv > 0x0560)
            *heroyv = 0x0560;
    }
    if (*heroyv > 0)
        fallspeed = *heroyv;

    objCollidMap(idx);
    objUpdateXY(idx);
    herowasground = heroground;
    heroground = heroobj->tilestand != 0;
    if (heroground)
    {
        coyote = 6;
        stompchain = 0;
    }
    else if (coyote)
        coyote--;

    herox = *heroox;
    heroy = *herooy;
    if (herox < 4)
    {
        herox = 4;
        *heroox = 4;
    }
    // the boss arena closes behind the hero
    if (bossactive && herox < a_arenax + 4)
    {
        herox = a_arenax + 4;
        *heroox = herox;
        if (*heroxv < 0)
            *heroxv = 0;
    }
    if (herox > a_arenax + 256 - 36)
    {
        herox = a_arenax + 256 - 36;
        *heroox = herox;
    }

    if (heroground && !herowasground)
    {
        if (fallspeed > 0x0300)
        {
            landtimer = 6;
            sfx(SFX_LAND);
        }
        else
            landtimer = 3;
        fallspeed = 0;
    }

    // fell into a hazard: splash and spring back out
    if (heroy + 31 >= WATER_Y && !stagedone)
    {
        sfx(SFX_SPLAT);
        spawnSpark(herox + 8, WATER_Y - 14);
        if (!heroinvuln && herohp)
        {
            herohp--;
            heroinvuln = 90;
            sfx(SFX_HURT);
        }
        *heroyv = -0x0420;
        jumpcut = 1;
    }

    if (herothrow)
    {
        if (herothrow == ((weapon == W_RAPID) ? 7 : 11))
            fireWeapon();
        herothrow--;
    }
    if (heroinvuln)
        heroinvuln--;
    if (landtimer)
        landtimer--;

    // pick the animation frame
    heroanim++;
    speed = *heroxv;
    if (speed < 0)
        speed = -speed;
    if (stagedone && heroground)
        heroframe = F_CHEER;
    else if (heroinvuln > 70 || herohp == 0)
        heroframe = F_HURT;
    else if (herocrouch)
        heroframe = herothrow ? F_CROUCH_THROW : F_CROUCH;
    else if (herothrow)
        heroframe = F_THROW + (herothrow > 11 ? 0 : (herothrow > 5 ? 1 : 2));
    else if (!heroground)
    {
        if (*heroyv < -0x0100)
            heroframe = F_JUMP;
        else if (*heroyv < 0x0100)
            heroframe = F_APEX;
        else
            heroframe = F_FALL;
    }
    else if (landtimer)
        heroframe = F_LAND;
    else if (speed > 0x30)
    {
        // run cycle speed follows the actual running speed
        runphase += speed >> 3;
        heroframe = F_RUN + ((runphase >> 8) & 7);
    }
    else
    {
        runphase = 0x0100;    // first stride starts mid-step
        heroframe = F_IDLE + ((heroanim >> 4) & 3);
    }

    // camera leads in the direction the hero faces so foes show up early
    if (heroflip)
    {
        if (look > -LOOK_AHEAD)
            look -= (speed > 0x0100) ? 2 : 1;
    }
    else if (look < LOOK_AHEAD)
        look += (speed > 0x0100) ? 2 : 1;
    speed = (s16)herox + 16 + look;
    if (speed < 0)
        speed = 0;
    if (bossactive && speed < (s16)a_arenax + 128)
        speed = a_arenax + 128;
    mapUpdateCamera(speed, heroy);
}

// ---------------------------------------------------------------- foes
void foesReset(void)
{
    u16 *t = a_foetab;
    u8 n;
    nfoes = a_nfoes;
    nact = 0;
    refoes = 1;
    ffirst = 0;
    for (n = 0; n < nfoes; n++)
    {
        fkind[n] = t[0];
        ft[n] = stage * 3 + t[0] - 1;    // index into the behaviour tables
        fx[n] = t[1];
        fy[n] = t[2];
        fmin[n] = t[3];
        fmax[n] = t[4];
        fdir[n] = n & 1;
        fstate[n] = FOE_WALK;
        fhp[n] = foe_hp[ft[n]];
        ftimer[n] = n << 2;
        fhop[n] = 0;
        fhopv[n] = 0;
        fframe[n] = 0;
        t += 5;
    }
}

void foeKilled(u8 n, u16 x, u16 y, u8 kind)
{
    u8 pts = foe_pts[kind];
    // stomping several foes without landing doubles the points each time
    if (stompchain > 1)
        pts <<= (stompchain > 4 ? 3 : stompchain - 1);
    addScore(pts);
    kills++;
    if ((kills & 3) == 0)
        spawnDrop(x, fy[n], ITEM_STAR);
}

void foesUpdate(void)
{
    s16 dx, top, feet, hx, wl, wr, xl, yl, hop, hopv, lo, hi;
    u8 t, b, k, st, tm, dir, fr, n, dmg, hp, near, a, walk, step, mk, x0, x1, hh;
    feet = (s16)heroy + 31;
    hx = (s16)herox + 16;
    // only foes near the camera move. The list is rebuilt every fourth frame,
    // and the margin covers how far the camera can go in between.
    if ((frame & 3) == 0 || refoes)
    {
        refoes = 0;
        wl = (s16)x_pos - 64;
        wr = (s16)x_pos + 320;
        nact = 0;
        // foes are sorted by where they start, and none strays more than
        // about 100px from its patrol, so only a window of them needs a look
        while (ffirst < nfoes && (s16)fmax[ffirst] + 160 < wl)
            ffirst++;
        while (ffirst > 0 && (s16)fmax[ffirst - 1] + 160 >= wl)
            ffirst--;
        for (n = ffirst; n < nfoes; n++)
        {
            if ((s16)fmin[n] > wr + 160)
                break;
            if (fstate[n] == FOE_DEAD)
                continue;
            xl = (s16)fx[n];
            if (xl < wl || xl > wr)
                continue;
            actlist[nact] = n;
            nact++;
            if (nact == MAX_ACTIVE)
                break;
        }
    }
    for (a = 0; a < nact; a++)
    {
        n = actlist[a];
        st = fstate[n];
        if (st == FOE_DEAD)
            continue;
        xl = (s16)fx[n];
        k = fkind[n];
        t = ft[n];
        b = foe_beh[t];
        yl = (s16)fy[n];
        tm = ftimer[n];
        dir = fdir[n];
        hop = fhop[n];
        hopv = fhopv[n];
        fr = fframe[n];
        lo = fmin[n];
        hi = fmax[n];
        mk = foe_mask[t];
        dx = hx - (xl + (k == KIND_C ? 8 : 16));
        near = feet > yl - 40 && feet < yl + 8;    // hero on the same floor

        if (st == FOE_WALK)
        {
            if (tm)
                tm--;
            walk = 1;    // patrol back and forth between fmin and fmax
            switch (b)
            {
            case B_HOP:
                // hop now and then, more often with the hero close by
                if (tm == 0 && hop == 0 && hopv == 0)
                {
                    hopv = -0x0300;
                    tm = (dx > -64 && dx < 64) ? 40 : 90;
                }
                fr = (hop < 0) ? SF_C_ALT + ((frame >> 2) & 1) : SF_C + ((frame >> 3) & 1);
                break;
            case B_FLY:
                hop = bobtab[(frame >> 2) & 15] - 24;
                fr = SF_C + ((frame >> 2) & 1);
                // swoop at a hero passing underneath
                if (tm == 0 && dx > -40 && dx < 40 && feet > yl - 24)
                {
                    st = FOE_CHARGE;
                    tm = 60;
                }
                break;
            case B_ZIG:
                // weaves up and down through the air, drifting after the hero
                walk = 0;
                hop = bobtab[(frame >> 1) & 15];
                hop = (hop << 2) - 36;
                fr = SF_C + ((frame >> 2) & 1);
                if (frame & 1)
                {
                    if (dx > 4 && xl < hi + 40)
                    {
                        xl++;
                        dir = 1;
                    }
                    else if (dx < -4 && xl > lo - 40)
                    {
                        xl--;
                        dir = 0;
                    }
                }
                break;
            case B_DROP:
                // circles up high and lets something fall on the hero's head
                hop = bobtab[(frame >> 2) & 15] - 56;
                fr = SF_C_ALT + ((frame >> 2) & 1);
                if (dx > -160 && dx < 160)
                {
                    walk = 0;
                    if (dx > 2 && xl < hi + 32)
                    {
                        xl++;
                        dir = 1;
                    }
                    else if (dx < -2 && xl > lo - 32)
                    {
                        xl--;
                        dir = 0;
                    }
                    if (tm == 0 && dx > -14 && dx < 14)
                    {
                        bossShot(xl, yl + hop - 4, 0, 6, 1);
                        tm = 110;
                    }
                }
                break;
            case B_SCURRY:
                // darts along fast, stops to sniff, and turns to dash at the hero
                walk = 0;
                if (tm)
                    fr = SF_C;
                else
                {
                    if (dir)
                        xl += 2;
                    else
                        xl -= 2;
                    fr = SF_C + ((frame >> 1) & 1);
                    if (xl >= hi)
                    {
                        dir = 0;
                        tm = 12 + (rnd() & 31);
                    }
                    else if (xl <= lo)
                    {
                        dir = 1;
                        tm = 12 + (rnd() & 31);
                    }
                    else if (near && dx > -96 && dx < 96 && (rnd() & 31) == 0)
                        dir = (dx > 0) ? 1 : 0;
                }
                break;
            case B_BOUNCE:
                // never stops bouncing, and steers at the hero on every landing
                walk = 0;
                if (hop == 0 && hopv == 0)
                {
                    hopv = -0x0380;
                    if (dx > -128 && dx < 128)
                        dir = (dx > 0) ? 1 : 0;
                }
                if (dir)
                    xl++;
                else
                    xl--;
                if (xl >= hi + 48)
                    dir = 0;
                if (xl <= lo - 48)
                    dir = 1;
                fr = SF_C + ((frame >> 3) & 1) + (hop < -8 ? 2 : 0);
                break;
            case B_SHOOT:
                // stops, winds up and throws at a hero in range
                fr = (frame >> 4) & 3;
                if (tm == 0 && dx > -150 && dx < 150 && feet > yl - 96 && feet < yl + 48)
                {
                    st = FOE_CHARGE;
                    tm = 40;
                    dir = (dx > 0) ? 1 : 0;
                    walk = 0;
                }
                break;
            case B_POUNCE:
                // crouches, then leaps at the hero
                fr = (frame >> 3) & 3;
                if (tm == 0 && near && dx > -100 && dx < 100)
                {
                    st = FOE_CHARGE;
                    tm = 18;
                    dir = (dx > 0) ? 1 : 0;
                    walk = 0;
                    sfx(SFX_BLEAT);
                }
                break;
            case B_GUARD:
                // turns to face the hero with its guard up and edges closer
                if (near && dx > -120 && dx < 120)
                {
                    walk = 0;
                    dir = (dx > 0) ? 1 : 0;
                    fr = 4;
                    if ((frame & 3) == 0 && (dx > 24 || dx < -24))
                    {
                        if (dir && xl < hi + 24)
                            xl++;
                        if (!dir && xl > lo - 24)
                            xl--;
                    }
                }
                else
                    fr = (frame >> 4) & 3;
                break;
            case B_CHASE:
                // gives chase, honking, a little slower than the hero runs
                if (near && dx > -128 && dx < 128)
                {
                    walk = 0;
                    dir = (dx > 0) ? 1 : 0;
                    fr = 4 + ((frame >> 2) & 1);
                    step = ((frame & 3) == 0) ? 2 : 1;
                    if (dir && xl < hi + 40)
                        xl += step;
                    if (!dir && xl > lo - 40)
                        xl -= step;
                    if ((frame & 63) == 0)
                        sfx(SFX_BLEAT);
                }
                else
                    fr = (frame >> 3) & 3;
                break;
            default:    // B_WALK, B_CHARGE
                fr = (frame >> (mk > 1 ? 4 : 3)) & 3;
                // spot the hero in front on the same floor: lower the head and charge
                if (b == B_CHARGE && near && tm == 0)
                {
                    if ((dir && dx > 0 && dx < 112) || (!dir && dx < 0 && dx > -112))
                    {
                        st = FOE_CHARGE;
                        tm = (foe_rush[t] > 1) ? 56 : 80;
                        sfx(SFX_BLEAT);
                    }
                }
                break;
            }
            if (walk)
            {
                if ((frame & mk) == 0)
                {
                    if (dir)
                        xl++;
                    else
                        xl--;
                }
                if (xl >= hi)
                    dir = 0;
                if (xl <= lo)
                    dir = 1;
            }
        }
        else if (st == FOE_CHARGE)
        {
            if (b == B_POUNCE)
            {
                if (tm > 100)
                {
                    // in the air
                    fr = 5;
                    if (dir && xl < hi + 40)
                        xl += 2;
                    if (!dir && xl > lo - 40)
                        xl -= 2;
                    if (hop == 0 && hopv == 0)
                    {
                        st = FOE_WALK;
                        tm = 50;
                    }
                }
                else
                {
                    fr = 4;
                    tm--;
                    if (tm == 0)
                    {
                        hopv = -0x0400;
                        tm = 200;
                    }
                }
            }
            else
            {
                if (b == B_FLY)
                {
                    // dive towards the hero's height, then climb back up
                    if (tm > 30)
                    {
                        if (yl + hop < feet - 6)
                            hop += 2;
                        xl += (dx > 0) ? 1 : -1;
                    }
                    else if (hop > -24)
                        hop--;
                    fr = SF_C_ALT + ((frame >> 1) & 1);
                }
                else if (b == B_SHOOT)
                {
                    fr = (tm > 14) ? 4 : 5;
                    if (tm == 14)
                    {
                        if (boss_shotgrav[stage])
                        {
                            // lobbed in an arc that comes down on the hero
                            wl = dx / 3;
                            if (wl > 48)
                                wl = 48;
                            if (wl < -48)
                                wl = -48;
                            bossShot(xl + 8, yl - 40, wl, -48, 1);
                        }
                        else    // straight, at head height: crouch under it
                            bossShot(xl + (dir ? 20 : -4), yl - 30, dir ? 40 : -40, 0, 0);
                    }
                }
                else
                {
                    fr = 4 + ((frame >> 2) & 1);
                    if (tm < 44)    // short wind-up, then a run
                    {
                        step = foe_rush[t];
                        if (step == 1)
                            step = 1 + (frame & 1);
                        if (dir && xl < hi + 24)
                            xl += step;
                        if (!dir && xl > lo - 24)
                            xl -= step;
                    }
                    else
                        fr = 4;
                }
                tm--;
                if (tm == 0)
                {
                    st = FOE_WALK;
                    tm = (b == B_FLY) ? 90 : ((b == B_SHOOT) ? 80 + (rnd() & 63) : 70);
                }
            }
        }
        else    // FOE_HURT
        {
            fr = (k == KIND_C) ? SF_C_HURT : 6;
            if (dir)
                xl++;
            else
                xl--;
            tm--;
            if (tm == 0)
            {
                if (fhp[n] == 0)
                {
                    st = FOE_DEAD;
                    spawnSpark(xl + (k == KIND_C ? 0 : 8), yl + hop - 20);
                    foeKilled(n, xl + (k == KIND_C ? 0 : 8), yl, k);
                }
                else
                {
                    st = FOE_WALK;
                    tm = 40;
                }
            }
        }

        if ((b == B_HOP || b == B_POUNCE || b == B_BOUNCE) && (hop || hopv))
        {
            hop += hopv >> 8;
            hopv += 0x0030;
            if (hop >= 0)
            {
                hop = 0;
                hopv = 0;
            }
        }

        if (st != FOE_HURT && st != FOE_DEAD)
        {
            x0 = foe_x0[k];
            x1 = foe_x1[k];
            hh = foe_h[k];
            top = yl + hop - hh;
            // hit by a shot
            dmg = nshots ? shotHits(xl + x0, top - 2, xl + x1, yl + hop) : 0;
            // a guard blocks ordinary shots from the front: bombs, charged
            // shots, stomps and hits from behind get through
            if (dmg && b == B_GUARD && dir == (dx > 0 ? 1 : 0))
            {
                if (dmg < (hero == HERO_WES ? 4 : 3))
                {
                    dmg = 0;
                    spawnSpark(xl + (dir ? 22 : -6), top + 2);
                    sfx(SFX_LAND);
                }
            }
            if (!dmg && herohp && dx > -40 && dx < 40 && hx + 6 > xl + x0 && hx - 6 < xl + x1 && feet > top &&
                (s16)heroy + herotop < yl + hop)
            {
                // touching the hero: stomp from above, otherwise the foe wins
                if (*heroyv > 0 && feet < top + 10)
                {
                    heroBounce((pad0 & KEY_B) ? -0x0440 : -0x0300);    // hold B for a big bounce
                    stompchain++;
                    dmg = 2;
                    sfx(SFX_STOMP);
                    spawnSpark(xl + (k == KIND_C ? 0 : 8), top - 8);
                }
                else
                    heroHurt(xl + 16);
            }
            if (dmg)
            {
                hp = fhp[n];
                fhp[n] = (hp <= dmg) ? 0 : hp - dmg;
                st = FOE_HURT;
                tm = 14;
                dir = dx < 0;    // knocked away from the hero
                sfx(SFX_BLEAT);
            }
        }

        fx[n] = xl;
        fstate[n] = st;
        ftimer[n] = tm;
        fdir[n] = dir;
        fhop[n] = hop;
        fhopv[n] = hopv;
        fframe[n] = fr;
    }
}

// ---------------------------------------------------------------- props, pickups, checkpoints
void propsReset(void)
{
    u16 *t = a_proptab;
    u8 n;
    nprops = a_nprops;
    prfirst = 0;
    prend = 0;
    for (n = 0; n < nprops; n++)
    {
        prx[n] = t[0];
        pry[n] = t[1];
        pritem[n] = t[2];
        prstate[n] = PR_WHOLE;
        prshake[n] = 0;
        t += 3;
    }
    for (n = 0; n < 6; n++)
        heartgot[n] = 0;
}

void propBreak(u8 n)
{
    prstate[n] = PR_GONE;
    spawnSpark(prx[n], pry[n] - 16);
    spawnDrop(prx[n], pry[n], pritem[n]);
    addScore(5);
    sfx(SFX_CRACK);
}

void propsUpdate(void)
{
    s16 x, y, feet, hx;
    u8 n, dmg;
    s16 lo, hi;
    // props are sorted by x, so only the run on screen is looked at
    lo = (s16)x_pos - 16;
    hi = (s16)x_pos + 256;
    n = prfirst;
    while (n > 0 && (s16)prx[n - 1] >= lo)
        n--;
    while (n < nprops && (s16)prx[n] < lo)
        n++;
    prfirst = n;
    n = prend;
    if (n < prfirst)
        n = prfirst;
    while (n > prfirst && (s16)prx[n - 1] > hi)
        n--;
    while (n < nprops && (s16)prx[n] <= hi)
        n++;
    prend = n;

    feet = (s16)heroy + 31;
    hx = (s16)herox + 16;
    for (n = prfirst; n < prend; n++)
    {
        if (prstate[n] == PR_GONE)
            continue;
        x = (s16)prx[n];
        y = (s16)pry[n];
        if (prshake[n])
            prshake[n]--;
        dmg = nshots ? shotHits(x + 1, y - 15, x + 15, y) : 0;
        if (dmg)
        {
            if (prstate[n] == PR_WHOLE && dmg < 3)
            {
                prstate[n] = PR_CRACKED;
                prshake[n] = 8;
                sfx(SFX_STOMP);
            }
            else
                propBreak(n);
            continue;
        }
        // stomping a prop smashes it
        if (*heroyv > 0 && hx + 6 > x && hx - 6 < x + 16 && feet > y - 16 && feet < y - 8)
        {
            heroBounce(-0x0300);
            propBreak(n);
        }
    }
}

void collect(u8 item, u16 x, u16 y)
{
    spawnSpark(x, y);
    switch (item)
    {
    case ITEM_STAR:
        addScore(50);
        sfx(SFX_DING);
        break;
    case ITEM_HEART:
        if (herohp < hpmax[hero])
            herohp++;
        else
            addScore(10);
        sfx(SFX_HEART);
        break;
    case ITEM_1UP:
        if (lives < 99)
            lives++;
        sfx(SFX_ONEUP);
        break;
    default:
        weapon = item - ITEM_SPREAD + W_SPREAD;
        sfx(SFX_POWERUP);
        break;
    }
}

void dropsUpdate(void)
{
    s16 hx, hy, x, y;
    u8 n;
    if (!ndrops)
        return;
    hx = (s16)herox + 16;
    hy = (s16)heroy + 16;
    for (n = 0; n < MAX_DROPS; n++)
    {
        if (!dralive[n])
            continue;
        drtime[n]++;
        if (drvy[n] || (dry[n] >> 4) < drfloor[n] - 16)
        {
            dry[n] += drvy[n];
            drvy[n] += 3;
            if ((dry[n] >> 4) >= drfloor[n] - 16 && drvy[n] > 0)
            {
                dry[n] = (drfloor[n] - 16) << 4;
                drvy[n] = 0;
            }
        }
        x = (s16)drx[n] + 8;
        y = (dry[n] >> 4) + 8;
        if (drtime[n] > 12 && x > hx - 16 && x < hx + 16 && y > hy - 20 && y < hy + 20)
        {
            dralive[n] = 0;
            ndrops--;
            collect(dritem[n], drx[n], dry[n] >> 4);
            continue;
        }
        // stars and hearts don't wait around forever
        if (drtime[n] > 600 && dritem[n] <= ITEM_HEART)
        {
            dralive[n] = 0;
            ndrops--;
        }
    }
}

u8 hvis[6], nhvis;

void heartsUpdate(void)
{
    u16 hx, hy, *t;
    u8 n;
    nhvis = 0;
    t = a_hearttab;
    for (n = 0; n < a_nhearts; n++, t += 2)
    {
        if (heartgot[n])
            continue;
        hx = t[0];
        if (hx + 16 < x_pos || hx > x_pos + 256)
            continue;
        hy = t[1];
        hvis[nhvis] = n;
        nhvis++;
        if (herox + 22 > hx + 2 && herox + 10 < hx + 14 && heroy + 31 > hy && heroy + heroyofs < hy + 16)
        {
            heartgot[n] = 1;
            collect(ITEM_HEART, hx, hy);
        }
    }
}

void checkpointsUpdate(void)
{
    u8 k;
    for (k = 0; k < 2; k++)
    {
        if (checkpoint <= k && herox + 16 >= cpx[k])
        {
            checkpoint = k + 1;
            sfx(SFX_DING);
            spawnSpark(cpx[k], cpy[k] - 24);
            hudTextPal(9, 8, "CHECKPOINT!", 2);
            hudrows = 9;
            cptimer = 90;
        }
    }
    if (cptimer)
    {
        cptimer--;
        if (cptimer == 0)
        {
            hudClearRow(8);
            hudrows = 9;
        }
    }
}

// ---------------------------------------------------------------- drawing
void drawItem(s16 x, s16 y, u8 f, u8 attr)
{
    drawSmall(x - (s16)x_pos, y - (s16)y_pos, f, ATTR_SPRITE(PAL_ITEMS) | attr, &items_pic);
}

u8 itemFrame(u8 item)
{
    if (item == ITEM_STAR)
        return IF_STAR + ((frame >> 3) & 1);
    if (item == ITEM_1UP)
        return IF_1UP;
    return IF_WEAPON + item - ITEM_SPREAD;
}

void drawWorld(void)
{
    Shot *sh;
    s16 sx, sy, x, y;
    u8 k, attr, n, f;
    nbig = BIG_FIRST;
    nsmall = SMALL_FIRST;

    // hero (blinks while invulnerable)
    sx = (s16)herox - (s16)x_pos;
    sy = (s16)heroy - (s16)y_pos;
    if (heroinvuln && (heroinvuln & 4))
        sy = 240;
    drawBig(sx, sy, heroframe, ATTR_SPRITE(hero) | (heroflip ? 0x40 : 0), hero == HERO_JON ? &jon_pic : &wes_pic);
    // charging: sparks gather at the throwing hand, then it flashes when ready
    if (herocharge > 12)
    {
        x = sx + (heroflip ? 0 : 20);
        y = sy + (herocrouch ? 18 : 9);
        if (herocharge >= CHARGE_FULL)
            drawSmall(x - 2, y - 2, IF_SPARKLE + ((frame >> 1) & 1), ATTR_SPRITE(PAL_ITEMS) | OBJ_PRIO(3), &items_pic);
        else if (frame & 2)
            drawSmall(x + ((frame & 4) ? -3 : 3), y + ((frame & 8) ? -3 : 3), SF_SPARK + ((frame >> 2) & 1),
                      ATTR_SPRITE(PAL_FOE_A) | OBJ_PRIO(3), a_small);
    }

    if (bossactive)
        bossDraw();
    if (nbshots)
        bshotsDraw();

    for (j = 0; j < nact; j++)
    {
        n = actlist[j];
        if (fstate[n] == FOE_DEAD)
            continue;
        k = fkind[n];
        sx = (s16)fx[n] - (s16)x_pos;
        if (sx < -32 || sx > 256)
            continue;
        attr = fdir[n] ? 0 : 0x40;
        if (fstate[n] == FOE_HURT)
            attr ^= 0x40;    // still faces the hero while knocked back
        if (k == KIND_C)
            drawSmall(sx, (s16)fy[n] + fhop[n] - 16 - (s16)y_pos, fframe[n], ATTR_SPRITE(PAL_FOE_A) | attr, a_small);
        else if (k == KIND_B)
            drawBig(sx, (s16)fy[n] + fhop[n] - 32 - (s16)y_pos, 7 + fframe[n], ATTR_SPRITE(PAL_FOE_B) | attr, a_foes);
        else
            drawBig(sx, (s16)fy[n] + fhop[n] - 32 - (s16)y_pos, fframe[n], ATTR_SPRITE(PAL_FOE_A) | attr, a_foes);
    }

    // shots
    sh = shots;
    for (n = nshots ? 0 : MAX_SHOTS; n < MAX_SHOTS; n++, sh++)
    {
        if (!sh->alive)
            continue;
        // screen position of the shot's centre
        x = (s16)(sh->x >> 4) - (s16)x_pos;
        y = (sh->y >> 4) - (s16)y_pos;
        switch (sh->kind)
        {
        case SK_LOB:
            drawSmall(x - 6, y - 6, SF_SHOT + ((frame >> 2) & 1), ATTR_SPRITE(PAL_FOE_A), a_small);
            break;
        case SK_BOLT:
            drawSmall(x - 8, y - 8, IF_BOLT + ((frame >> 1) & 1), ATTR_SPRITE(PAL_ITEMS) | (sh->vx < 0 ? 0x40 : 0),
                      &items_pic);
            break;
        case SK_RANG:
            f = (frame >> 2) & 3;
            drawSmall(x - 8, y - 8, IF_RANG + (f & 1), ATTR_SPRITE(PAL_ITEMS) | ((f & 2) ? 0xC0 : 0), &items_pic);
            break;
        case SK_BOMB:
            drawSmall(x - 8, y - 8, IF_BOMB + ((frame >> 2) & 1), ATTR_SPRITE(PAL_ITEMS), &items_pic);
            break;
        default:
            // the blast: one 16x16 quarter mirrored four ways
            f = sh->life;
            f = IF_BOOM + (f > 14 ? 0 : (f > 7 ? 1 : 2));
            drawSmall(x - 16, y - 16, f, ATTR_SPRITE(PAL_ITEMS), &items_pic);
            drawSmall(x, y - 16, f, ATTR_SPRITE(PAL_ITEMS) | 0x40, &items_pic);
            drawSmall(x - 16, y, f, ATTR_SPRITE(PAL_ITEMS) | 0x80, &items_pic);
            drawSmall(x, y, f, ATTR_SPRITE(PAL_ITEMS) | 0xC0, &items_pic);
            if (sh->power)
            {
                // a charged blast is bigger: a second ring further out
                drawSmall(x - 30, y - 8, f, ATTR_SPRITE(PAL_ITEMS), &items_pic);
                drawSmall(x + 14, y - 8, f, ATTR_SPRITE(PAL_ITEMS) | 0x40, &items_pic);
                drawSmall(x - 8, y - 30, f, ATTR_SPRITE(PAL_ITEMS), &items_pic);
                drawSmall(x - 8, y + 14, f, ATTR_SPRITE(PAL_ITEMS) | 0xC0, &items_pic);
            }
            break;
        }
        // charged shots leave a trail of sparks
        if (sh->power && (frame & 1) && sh->kind != SK_BOOM)
            drawSmall(x - 8 - (sh->vx >> 3), y - 8, SF_SPARK + ((frame >> 1) & 1), ATTR_SPRITE(PAL_FOE_A) | OBJ_PRIO(3),
                      a_small);
    }
    for (n = nsparks ? 0 : MAX_SPARKS; n < MAX_SPARKS; n++)
    {
        f = sptime[n];
        if (!f)
            continue;
        drawSmall((s16)spx[n] - (s16)x_pos, (s16)spy[n] - (s16)y_pos, SF_SPARK + ((12 - f) >> 2),
                  ATTR_SPRITE(PAL_FOE_A) | OBJ_PRIO(3), a_small);
        sptime[n] = f - 1;
        if (f == 1)
            nsparks--;
    }

    // pickups
    for (n = ndrops ? 0 : MAX_DROPS; n < MAX_DROPS; n++)
    {
        if (!dralive[n])
            continue;
        if (drtime[n] > 480 && dritem[n] <= ITEM_HEART && (frame & 4))
            continue;
        y = (dry[n] >> 4) - (drvy[n] == 0 && ((frame >> 4) & 1) ? 1 : 0);
        if (dritem[n] == ITEM_HEART)
            drawSmall((s16)drx[n] - (s16)x_pos, y - (s16)y_pos, SF_HEART, ATTR_SPRITE(PAL_FOE_A), a_small);
        else
            drawItem(drx[n], y, itemFrame(dritem[n]), 0);
    }
    for (n = 0; n < nhvis; n++)
    {
        k = hvis[n];
        drawSmall((s16)a_hearttab[k * 2] - (s16)x_pos, (s16)a_hearttab[k * 2 + 1] - (s16)y_pos + ((frame >> 4) & 1),
                  SF_HEART, ATTR_SPRITE(PAL_FOE_A), a_small);
    }

    // props and checkpoint flags
    for (n = prfirst; n < prend; n++)
    {
        if (prstate[n] == PR_GONE)
            continue;
        x = (s16)prx[n];
        if (prshake[n] & 2)
            x++;
        drawItem(x, (s16)pry[n] - 16, IF_PROP + stage * 2 + prstate[n], 0);
    }
    for (n = 0; n < 2; n++)
    {
        x = (s16)cpx[n] - (s16)x_pos;
        if (x > -16 && x < 256)
            drawSmall(x, (s16)cpy[n] - 16 - (s16)y_pos, checkpoint > n ? IF_FLAG_UP + ((frame >> 4) & 1) : IF_FLAG_DOWN,
                      ATTR_SPRITE(PAL_ITEMS), &items_pic);
    }
}

// ---------------------------------------------------------------- pause menu
char *const pause_opts[4] = {"CONTINUE", "LAST CHECKPOINT", "RESTART STAGE", "QUIT TO TITLE"};

void pauseDraw(u8 sel)
{
    u8 k;
    for (k = 0; k < 4; k++)
    {
        hudClearRow(12 + k * 2);
        hudTextPal(9, 12 + k * 2, pause_opts[k], k == sel ? 2 : 0);
        if (k == sel)
            hudText(7, 12 + k * 2, ">");
    }
    hudrows = 20;
}

// returns 0 continue, 1 last checkpoint, 2 restart, 3 quit
u8 pauseMenu(void)
{
    u8 sel = 0, k;
    spcPauseMusic();
    sfx(SFX_SELECT);
    hudTextPal(13, 9, "PAUSED", 2);
    pauseDraw(sel);
    waitFrame();
    hudFlush();
    setBrightness(9);    // dim the stage behind the menu
    while (1)
    {
        waitFrame();
        hudFlush();    // first thing in the vblank, before the redraw below
        padpressed = padsDown(0);
        if (padpressed & KEY_DOWN)
        {
            sel = (sel + 1) & 3;
            pauseDraw(sel);
            sfx(SFX_SELECT);
        }
        if (padpressed & KEY_UP)
        {
            sel = (sel - 1) & 3;
            pauseDraw(sel);
            sfx(SFX_SELECT);
        }
        if (padpressed & (KEY_START | KEY_A | KEY_B))
            break;
    }
    for (k = 9; k < 20; k++)
        hudClearRow(k);
    hudrows = 20;
    waitFrame();
    hudFlush();
    setBrightness(15);
    spcResumeMusic();
    // swallow the button so the hero doesn't jump straight away
    padsDown(0);
    return sel;
}

// ---------------------------------------------------------------- stage flow
void stageLoad(void)
{
    setScreenOff();
    setBrightness(0);
    oamClear(0, 0);
    loadStageAssets(stage);

    setPalette(a_bgpal, 0, 256);
    setPalette(&ui_pal, 0, 24);
    setPalette(a_bgpal, 0, 2);                 // stage backdrop colour
    setPalette(&jon_pal, 128, 32);
    setPalette(&wes_pal, 144, 32);
    setPalette(a_spra, 160, 32);
    setPalette(&items_pal, 176, 32);
    setPalette(a_sprb, 208, 32);
    setPalette(a_bosspal, 224, 32);
    dmaCopyVram(a_bg1pic, 0x2000, a_bg1size);
    dmaCopyVram(a_bg2pic, 0x4000, a_bg2size);
    dmaCopyVram(a_bg2map, 0x7000, 64 * 32 * 2);
    dmaCopyVram(&font_pic, 0x6000, (&font_pic_end - &font_pic));
    screenSetup();
    oamInitDynamicSprite(0x0000, 0x1000, 0, 0, OBJ_SIZE16_L32);
    spritesReset();
}

// newstage 1: entering the stage (props and checkpoints reset); 0: back at
// the last checkpoint after losing a life or from the pause menu
void stageStart(u8 newstage)
{
    u16 sx, sy;
    u8 n;
    stageLoad();

    if (hero == HERO_JON)
    {
        // Jon: taller, floatier, jumps higher
        hero_accel = 0x0028;
        hero_maxspeed = 0x0160;
        hero_jump = 0x0450;
        heroyofs = 3;
    }
    else
    {
        // Wes: quicker on his feet, a little lower jump, hits harder
        hero_accel = 0x0034;
        hero_maxspeed = 0x0190;
        hero_jump = 0x03F0;
        heroyofs = 6;
    }
    if (newstage)
    {
        checkpoint = 0;
        propsReset();
    }
    cpx[0] = a_cptab[0];
    cpy[0] = a_cptab[1];
    cpx[1] = a_cptab[2];
    cpy[1] = a_cptab[3];
    herohp = hpmax[hero];
    heroinvuln = checkpoint ? 60 : 0;
    herothrow = 0;
    herocharge = 0;
    herocrouch = 0;
    heroflip = 0;
    heroground = 0;
    herodead = 0;
    coyote = 0;
    jumpbuf = 0;
    landtimer = 0;
    stompchain = 0;
    look = 0;
    stagedone = 0;
    cptimer = 0;
    nshots = 0;
    for (n = 0; n < MAX_SHOTS; n++)
        shots[n].alive = 0;
    for (n = 0; n < MAX_SPARKS; n++)
        sptime[n] = 0;
    for (n = 0; n < MAX_DROPS; n++)
        dralive[n] = 0;
    nsparks = 0;
    ndrops = 0;
    foesReset();
    bossInit();
    objInitEngine();
    objInitFunctions(0, &heroinit, &heroupdate, NULL);
    objLoadObjects(a_hero);
    mapLoad(a_map, a_tiledef, a_tileprop);

    if (checkpoint)
    {
        if (checkpoint == 3)
        {
            sx = a_arenax - 40;
            sy = 120;
            // the foes before the arena stay beaten
            for (n = 0; n < nfoes; n++)
                fstate[n] = FOE_DEAD;
        }
        else
        {
            sx = cpx[checkpoint - 1] + 8;
            sy = cpy[checkpoint - 1] - 40;
        }
        *heroox = sx;
        *herooy = sy;
        herox = sx;
        heroy = sy;
        // point the camera at the checkpoint before the first frame, or the
        // object engine leaves the hero (off camera) asleep
        mapUpdateCamera(sx + 16, sy);
        mapUpdate();
    }

    hudAll();
    hudrows = 32;
    hudFlush();

    playMusic(MOD_STAGE1 + stage);
    setScreenOn();
}

void stageClearText(void)
{
    u16 bonus = (u16)herohp * 50;
    hudTextPal(10, 8, "STAGE CLEAR!", 2);
    hudText(8, 10, "HEART BONUS");
    hudNumber(20, 10, bonus, 4);
    hudText(24, 10, "0");
    addScore(bonus);
    hudrows = 12;
}

// returns STAGE_CLEAR, or STAGE_GAMEOVER / STAGE_QUIT; restarts and
// respawns are handled in here
u8 stageLoop(void)
{
    u16 endtimer = 0;
    u8 first = 1, choice;
    while (1)
    {
        frame++;
        mapUpdate();
        objUpdateAll();
        foesUpdate();
        shotsUpdate();
        dropsUpdate();
        // props and hearts sit still, so they take turns
        if (frame & 1)
            propsUpdate();
        else
            heartsUpdate();
        checkpointsUpdate();
        if (bossactive)
            bossUpdate();
        if (nbshots)
            bshotsUpdate();

        if (herohp != lasthp)
            hudHearts();
        if (lives != lastlives)
            hudLives();
        if (score != lastscore)
            hudScore();
        if (weapon != lastweapon)
            hudWeapon();

        // reaching the arena wakes the boss
        if (!bossactive && !bossdead && herox >= a_arenax + 40)
        {
            bossStart();
            checkpoint = 3;
        }

        if (bossdead && !stagedone)
        {
            stagedone = 1;
            addScore(500);
            playMusic(MOD_CLEAR);
            stageClearText();
        }
        if (stagedone)
        {
            endtimer++;
            if (endtimer > 330 || (endtimer > 60 && (padsDown(0) & KEY_START)))
                return STAGE_CLEAR;
        }
        else if (herohp == 0)
        {
            endtimer++;
            if (endtimer == 1)
            {
                spcStop();
                weapon = W_LOB;
                lives--;
                hudTextPal(12, 8, lives ? "OUCH!" : "GAME OVER", 2);
                hudrows = 9;
            }
            if (endtimer > 120)
            {
                if (lives == 0)
                    return STAGE_GAMEOVER;
                fadeOut();
                stageStart(0);
                endtimer = 0;
                first = 1;
                continue;
            }
        }
        else if (padpressed & KEY_START)
        {
            choice = pauseMenu();
            if (choice == 3)
                return STAGE_QUIT;
            if (choice)
            {
                fadeOut();
                if (choice == 2)
                    checkpoint = 0;    // from the top, but broken props stay broken
                stageStart(0);
                first = 1;
                continue;
            }
        }

        drawWorld();
        endFrame();
        mapVblank();
        bgSetScroll(1, x_pos >> 1, 0);
        hudFlush();
        if (first)
        {
            first = 0;
            fadeIn();
        }
    }
}
