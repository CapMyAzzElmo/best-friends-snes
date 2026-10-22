/*---------------------------------------------------------------------------------

    COMRADES - the end-of-stage bosses

    Every boss is a 64x64 sprite (four 32x32 quadrants) driven by a short
    list of moves that loops. Each boss has its own signature moves, and a
    second, angrier list once it is down to half health.

    The shot pool here also serves the stage foes that throw or drop things.

---------------------------------------------------------------------------------*/
#include "game.h"

#define M_WALK 0
#define M_CHARGE 1
#define M_JUMP 2
#define M_ARC 3
#define M_WAVE 4        // high and low waves along the floor: crouch or jump
#define M_HOVER 5
#define M_SWOOP 6
#define M_DROP 7
#define M_RAMPAGE 8     // wall to wall charges that shake debris loose, then dizzy
#define M_FAN 9         // a spread of shots
#define M_BLOCK 10      // arms up, shots from the front bounce off, then a lunge
#define M_RAIN 11       // things fall from the sky across the arena
#define M_ZAG 12        // bounces around the arena diagonally
#define M_GAVEL 13      // ORDER: a sweep of falling gavels with one safe gap
#define M_TELEPORT 14   // vanishes, appears over the hero, and drops
#define M_CLOCK 15      // a ring of shots in every direction, twice
#define M_PENDULUM 16   // swings low across the arena: crouch under it
#define M_DIZZY 17      // (after a rampage) seeing stars: free hits

#define BF_IDLE 0
#define BF_ATTACK 2
#define BF_HURT 3
#define SF_BSHOT 11
#define GROUND 192
#define SKY 116
#define MAX_BSHOTS 8

const u8 boss_hp[6] = {16, 18, 20, 16, 22, 22};
const u8 boss_fly[6] = {0, 0, 0, 1, 0, 1};
// four moves, then four more once the boss is down to half health
const u8 boss_moves[48] = {
    M_WALK, M_CHARGE, M_WALK, M_JUMP, M_RAMPAGE, M_WALK, M_JUMP, M_CHARGE,              // Champion Bull
    M_WAVE, M_WALK, M_FAN, M_JUMP, M_WAVE, M_FAN, M_WAVE, M_JUMP,                       // Feedback
    M_WALK, M_BLOCK, M_ARC, M_CHARGE, M_BLOCK, M_ARC, M_CHARGE, M_JUMP,                 // the Bouncer
    M_HOVER, M_SWOOP, M_RAIN, M_ZAG, M_ZAG, M_RAIN, M_SWOOP, M_FAN,                     // Pigeon King
    M_GAVEL, M_WALK, M_TELEPORT, M_ARC, M_TELEPORT, M_GAVEL, M_TELEPORT, M_JUMP,        // the Judge
    M_PENDULUM, M_CLOCK, M_SWOOP, M_DROP, M_CLOCK, M_PENDULUM, M_CLOCK, M_ZAG};         // Father Time
// shots: 1 = falls under gravity (the stage foes that throw use this too)
const u8 boss_shotgrav[6] = {1, 0, 1, 1, 1, 0};
char *const boss_name[6] = {"CHAMPION BULL", "FEEDBACK", "THE BOUNCER", "PIGEON KING", "THE JUDGE",
                            "FATHER TIME"};
// sixteen directions, 22.5 degrees apart, at shot speed (1/16 px per frame)
const s8 ring_vx[16] = {36, 33, 25, 14, 0, -14, -25, -33, -36, -33, -25, -14, 0, 14, 25, 33};
const s8 ring_vy[16] = {0, 14, 25, 33, 36, 33, 25, 14, 0, -14, -25, -33, -36, -33, -25, -14};
// one pendulum swing: across the arena and down through the middle
const u8 swing_x[33] = {0, 0, 2, 4, 7, 11, 16, 21, 27, 34, 41, 49, 57, 65, 74, 83, 92,
                        101, 110, 119, 127, 135, 143, 150, 157, 163, 168, 173, 177, 180, 182, 184, 184};
const u8 swing_y[33] = {0, 5, 11, 16, 21, 26, 31, 36, 40, 43, 47, 49, 52, 54, 55, 56, 56,
                        56, 55, 54, 52, 49, 47, 43, 40, 36, 31, 26, 21, 16, 11, 5, 0};

u8 bossactive, bossdead;
u8 bhp, bmove, bstep, bdir, binv, bframe, bdying, bintro;
u8 bangry, bguard, bghost, bcount, bgap;
u16 btimer;
u16 bx16;          // left edge, 1/16 px
s16 by16;          // feet, 1/16 px
s16 bvx, bvy;      // 1/16 px per frame
u8 bfly, lastbhp;
typedef struct
{
    u16 x;
    s16 y, vx, vy;    // 1/16 px
    u8 alive, grav;
} BShot;
BShot bshots[MAX_BSHOTS];    // fast.asm knows this layout
u8 bn, nbshots;
s16 bspx, bspy, bslim;
u16 bhit, bland;
void bshotsMove(void);

void bossInit(void)
{
    bossactive = 0;
    bossdead = 0;
    bdying = 0;
    nbshots = 0;
    bhit = 0;
    bland = 0;
    for (bn = 0; bn < MAX_BSHOTS; bn++)
        bshots[bn].alive = 0;
}

void hudBossBar(void)
{
    u8 cells, k;
    cells = (bhp * 10 + boss_hp[stage] - 1) / boss_hp[stage];
    for (k = 0; k < 10; k++)
        hud[3 * 32 + 20 + k] = (k < cells ? 0x42 : 0x43) | 0x2000 | (1 << 10);
    huddirty = 1;
    lastbhp = bhp;
}

void bossStart(void)
{
    bossactive = 1;
    bfly = boss_fly[stage];
    bhp = boss_hp[stage];
    bmove = 0;
    bstep = 0;
    btimer = 0;
    bdir = 0;
    binv = 0;
    bangry = 0;
    bguard = 0;
    bghost = 0;
    bintro = 70;
    bx16 = (a_arenax + 256 - 84) << 4;
    by16 = -16 << 4;
    bvx = 0;
    bvy = 0;
    hudTextPal(1, 3, boss_name[stage], 2);
    hudBossBar();
    playMusic(MOD_BOSS);
    sfx(SFX_ROAR);
}

u16 bossX(void) { return bx16 >> 4; }
s16 bossFeet(void) { return by16 >> 4; }

// x, y: top left of the 16x16 shot in pixels; vx, vy in 1/16 px per frame
void bossShot(s16 x, s16 y, s16 vx, s16 vy, u8 grav)
{
    BShot *p = bshots;
    u8 k;
    for (k = 0; k < MAX_BSHOTS; k++, p++)
    {
        if (!p->alive)
        {
            p->alive = 1;
            p->x = x << 4;
            p->y = y << 4;
            p->vx = vx;
            p->vy = vy;
            p->grav = grav;
            nbshots++;
            sfx(SFX_THROW);
            return;
        }
    }
}

void faceHero(void)
{
    bdir = (herox + 16 > bossX() + 32) ? 1 : 0;
}

void nextMove(void)
{
    bstep = (bstep + 1) & 3;
    bmove = boss_moves[stage * 8 + bangry + bstep];
    btimer = 0;
    bvx = 0;
    bvy = 0;
    bcount = 0;
    bguard = 0;
    bghost = 0;
    faceHero();
}

// move the boss towards a target feet height (flyers)
void flyTo(s16 ty, s16 speed)
{
    s16 fy = bossFeet();
    if (fy < ty - 1)
        by16 += speed;
    else if (fy > ty + 1)
        by16 -= speed;
}

// a shot from the boss's middle in ring direction d
void ringShot(s16 cx, s16 fy, u8 d)
{
    bossShot(cx - 8, fy - 40, ring_vx[d & 15], ring_vy[d & 15], 0);
}

// something falls from the top of the screen at arena x
void skyShot(s16 x)
{
    bossShot(a_arenax + x, -16, 0, 0, 1);
}

void bossMove(void)
{
    s16 dx, hx, cx, fy;
    u16 left = (a_arenax + 4) << 4, right = (a_arenax + 256 - 68) << 4, tx;
    u8 k;
    hx = (s16)herox + 16;
    cx = (s16)bossX() + 32;
    dx = hx - cx;
    fy = bossFeet();
    btimer++;
    bframe = BF_IDLE + ((frame >> 4) & 1);

    switch (bmove)
    {
    case M_WALK:
        faceHero();
        if (btimer & 1)
            bx16 += bdir ? 16 : -16;
        if (btimer > 80)
            nextMove();
        break;
    case M_CHARGE:
        if (btimer < 36)
        {
            faceHero();
            bframe = (btimer & 4) ? BF_ATTACK : BF_IDLE;    // pawing the ground
            if (btimer == 1)
                sfx(SFX_ROAR);
        }
        else
        {
            bframe = BF_ATTACK;
            bx16 += bdir ? 52 : -52;
            if ((bdir && bx16 >= right) || (!bdir && bx16 <= left) || btimer > 160)
            {
                sfx(SFX_STOMP);
                nextMove();
            }
        }
        break;
    case M_RAMPAGE:
        if (btimer < 24)
        {
            bframe = (btimer & 4) ? BF_ATTACK : BF_IDLE;
            if (btimer == 1 && bcount == 0)
                sfx(SFX_ROAR);
        }
        else
        {
            bframe = BF_ATTACK;
            bx16 += bdir ? 60 : -60;
            if ((bdir && bx16 >= right) || (!bdir && bx16 <= left))
            {
                // slams the wall: the arena shakes and debris rains down
                sfx(SFX_CRASH);
                skyShot(16 + (rnd() & 127));
                skyShot(96 + (rnd() & 127));
                bdir ^= 1;
                bcount++;
                btimer = 10;
                if (bcount == 3)
                {
                    bmove = M_DIZZY;
                    btimer = 0;
                }
            }
        }
        break;
    case M_DIZZY:
        bframe = (btimer & 8) ? BF_HURT : BF_IDLE;
        if ((btimer & 15) == 0)
            spawnSpark(cx - 8 + ((btimer & 16) ? 12 : -12), fy - 64);
        if (btimer > 90)
            nextMove();
        break;
    case M_JUMP:
        if (btimer == 1)
        {
            faceHero();
            bvy = -0x58;
            bvx = dx / 3;            // reach the hero in about 50 frames
            if (bvx > 40)
                bvx = 40;
            if (bvx < -40)
                bvx = -40;
        }
        bframe = BF_ATTACK;
        by16 += bvy;
        bvy += 4;
        bx16 += bvx;
        if (by16 >= GROUND << 4 && bvy > 0)
        {
            by16 = GROUND << 4;
            sfx(SFX_STOMP);
            // the landing throws debris along the floor both ways
            bossShot(cx - 8, GROUND - 14, -36, 0, 0);
            bossShot(cx - 8, GROUND - 14, 36, 0, 0);
            nextMove();
        }
        break;
    case M_ARC:
        faceHero();
        if (btimer == 20 || btimer == 45 || btimer == 70)
        {
            bframe = BF_ATTACK;
            bossShot(cx - 8 + (bdir ? 16 : -16), fy - 52, dx / 3, -56, 1);
            if (bangry)    // angry: two more either side
            {
                bossShot(cx - 8, fy - 52, dx / 3 + 14, -60, 1);
                bossShot(cx - 8, fy - 52, dx / 3 - 14, -50, 1);
            }
        }
        if (btimer > 15 && (btimer % 25) < 8)
            bframe = BF_ATTACK;
        if (btimer > 100)
            nextMove();
        break;
    case M_WAVE:
        // a run of waves along the floor: low ones to jump, high ones to crouch under
        faceHero();
        if (btimer >= 20 && btimer <= 180 && ((btimer - 20) % 40) == 0)
        {
            k = (btimer - 20) / 40;
            bframe = BF_ATTACK;
            bossShot(cx - 8 + (bdir ? 24 : -24), ((0x12 >> k) & 1) ? GROUND - 34 : GROUND - 14,
                     bdir ? 44 : -44, 0, 0);
        }
        if (btimer > 15 && ((btimer - 20) % 40) < 8)
            bframe = BF_ATTACK;
        if (btimer > 200)
            nextMove();
        break;
    case M_FAN:
        faceHero();
        if (btimer == 20 || btimer == 60 || (bangry && btimer == 100))
        {
            bframe = BF_ATTACK;
            if (bfly)
            {
                // a spread aimed down at the floor
                for (k = 2; k <= 6; k++)
                    ringShot(cx, fy, k);
            }
            else
            {
                // a spread towards the hero: find the gap
                for (k = 0; k < 4; k++)
                    ringShot(cx, fy, bdir ? 14 + k : 10 - k);
            }
        }
        if (btimer > 15 && (btimer % 40) < 8)
            bframe = BF_ATTACK;
        if (btimer > 120)
            nextMove();
        break;
    case M_BLOCK:
        // arms up: edges closer and shrugs off shots from the front, then lunges
        if (btimer < 80)
        {
            bguard = 1;
            faceHero();
            bframe = BF_ATTACK;
            if ((btimer & 1) && (dx > 40 || dx < -40))
                bx16 += bdir ? 16 : -16;
        }
        else if (btimer < 104)
        {
            bguard = 0;
            if (btimer == 80)
                sfx(SFX_ROAR);
            bframe = BF_ATTACK;
            bx16 += bdir ? 64 : -64;
        }
        else
            nextMove();
        break;
    case M_HOVER:
        faceHero();
        flyTo(SKY, 24);
        if (btimer & 1)
            bx16 += (dx > 8) ? 16 : ((dx < -8) ? -16 : 0);
        by16 += ((btimer >> 3) & 1) ? 8 : -8;
        if (btimer > 90)
            nextMove();
        break;
    case M_SWOOP:
        bframe = BF_ATTACK;
        if (btimer < 50)
        {
            if (btimer == 1)
            {
                faceHero();
                sfx(SFX_ROAR);
                bvx = dx / 3;
            }
            bx16 += bvx;
            flyTo(GROUND, 64);
        }
        else if (btimer < 85)
            bframe = BF_IDLE;    // lands and catches its breath: the time to strike
        else
        {
            bframe = BF_IDLE;
            flyTo(SKY, 32);
            if (btimer > 130)
                nextMove();
        }
        break;
    case M_DROP:
        flyTo(SKY - 24, 24);
        bx16 += bdir ? 28 : -28;
        if ((bdir && bx16 >= right) || (!bdir && bx16 <= left))
            bdir ^= 1;
        if ((btimer % 22) == 10)
        {
            bframe = BF_ATTACK;
            bossShot(cx - 8, fy - 8, 0, 8, 1);
        }
        if (btimer > 120)
            nextMove();
        break;
    case M_RAIN:
        // up high, flapping, while things fall all over the arena
        flyTo(SKY - 40, 24);
        bframe = (btimer & 8) ? BF_ATTACK : BF_IDLE;
        if (btimer >= 20 && btimer <= 110 && (btimer & 7) == 0)
        {
            if ((btimer & 31) == 0)    // every fourth one falls right on the hero
                skyShot(hx - 8 - (s16)a_arenax);
            else
                skyShot(8 + (rnd() & 0xEF));
        }
        if (btimer > 140)
            nextMove();
        break;
    case M_ZAG:
        // bounces off the walls, the floor and the sky
        if (btimer == 1)
        {
            bvx = bdir ? 34 : -34;
            bvy = 30;
            sfx(SFX_ROAR);
        }
        bframe = BF_ATTACK;
        if (btimer < 170)
        {
            bx16 += bvx;
            by16 += bvy;
            if ((bvx > 0 && bx16 >= right) || (bvx < 0 && bx16 <= left))
                bvx = -bvx;
            if (bvy > 0 && fy >= GROUND)
            {
                bvy = -bvy;
                sfx(SFX_STOMP);
            }
            if (bvy < 0 && fy <= SKY - 36)
                bvy = -bvy;
        }
        else
        {
            bframe = BF_IDLE;
            flyTo(SKY, 32);
            if (btimer > 200)
                nextMove();
        }
        break;
    case M_GAVEL:
        // ORDER! Gavels fall in a sweep across the arena, with one gap to stand in
        if (btimer == 1)
        {
            faceHero();
            sfx(SFX_ROAR);
            bgap = rnd() & 7;
            if (bgap > 6)
                bgap = 3;
        }
        bframe = (btimer < 24) ? ((btimer & 4) ? BF_ATTACK : BF_IDLE) : BF_ATTACK;
        if (btimer == 24)
            sfx(SFX_CRASH);
        if (btimer >= 30 && btimer <= 30 + 6 * 9 && ((btimer - 30) % 9) == 0)
        {
            k = (btimer - 30) / 9;
            if (k != bgap)
                skyShot(bdir ? 8 + k * 36 : 224 - k * 36);
        }
        if (btimer > 120)
            nextMove();
        break;
    case M_TELEPORT:
        if (btimer < 30)
        {
            // fades out
            bghost = 1;
            bframe = BF_IDLE;
        }
        else if (btimer < 56)
        {
            // hangs over the hero's head, following
            if (btimer == 30)
            {
                by16 = 80 << 4;
                sfx(SFX_ROAR);
            }
            bghost = 1;
            bframe = BF_ATTACK;
            bx16 = (u16)(hx - 32) << 4;
        }
        else if (fy < GROUND)
        {
            bghost = 0;
            bframe = BF_ATTACK;
            bvy += 8;
            by16 += bvy;
            if (by16 >= GROUND << 4)
            {
                by16 = GROUND << 4;
                sfx(SFX_STOMP);
                bossShot(cx - 8, GROUND - 14, -40, 0, 0);
                bossShot(cx - 8, GROUND - 14, 40, 0, 0);
            }
        }
        else
        {
            bframe = BF_IDLE;
            if (bvy)
            {
                bvy = 0;
                btimer = 56;
            }
            if (btimer > 90)    // a moment to recover: the time to strike
                nextMove();
        }
        break;
    case M_CLOCK:
        // a ring of shots, then another between the first
        flyTo(SKY, 16);
        bframe = BF_IDLE;
        if (btimer == 30 || btimer == 70 || (bangry && btimer == 110))
        {
            bframe = BF_ATTACK;
            for (k = (btimer == 70) ? 1 : 0; k < 16; k += 2)
                ringShot(cx, fy, k);
        }
        if (btimer > 140)
            nextMove();
        break;
    case M_PENDULUM:
        // swings down across the arena twice, just over a crouching hero's head
        if (btimer == 1)
        {
            bcount = (bx16 > ((a_arenax + 96) << 4)) ? 1 : 0;    // start from the near side
            sfx(SFX_ROAR);
        }
        if (btimer < 30)
        {
            // move to the top of the swing
            tx = (a_arenax + 4 + swing_x[bcount ? 32 : 0]) << 4;
            if (bx16 + 64 < tx)
                bx16 += 64;
            else if (bx16 > tx + 64)
                bx16 -= 64;
            else
                bx16 = tx;
            flyTo(SKY, 32);
            if (btimer == 29 && bx16 != tx)
                btimer = 28;
        }
        else if (btimer < 30 + 33 * 2 * 3)
        {
            k = (btimer - 30) / 3;
            if (k >= 33)
                k = 65 - k;          // and back
            if (bcount)
                k = 32 - k;
            bx16 = (a_arenax + 4 + swing_x[k]) << 4;
            by16 = (SKY + swing_y[k]) << 4;
            bframe = BF_ATTACK;
            bdir = (btimer - 30 < 99) ? !bcount : bcount;
            if (btimer == 30 + 99)
                for (k = 3; k <= 5; k++)
                    ringShot(cx, fy, k);
        }
        else
        {
            flyTo(SKY, 24);
            if (btimer > 30 + 66 * 3 + 20)
                nextMove();
        }
        break;
    }
    if (bx16 < left)
        bx16 = left;
    if (bx16 > right)
        bx16 = right;
}

// thrown and dropped things from the boss and the stage foes
void bshotsUpdate(void)
{
    bshotsMove();
    if (bhit)
    {
        heroHurt(bhit);
        bhit = 0;
    }
    if (bland)
    {
        spawnSpark(bland, GROUND - 14);
        bland = 0;
    }
}

void bossUpdate(void)
{
    s16 top, feet, bx, fy;
    u8 dmg;

    if (!bossactive)
        return;

    if (bdying)
    {
        bdying--;
        bframe = BF_HURT;
        if ((bdying & 7) == 0)
        {
            spawnSpark(bossX() + (rnd() & 47), bossFeet() - 16 - (rnd() & 31));
            sfx(SFX_STOMP);
        }
        if (bdying == 0)
        {
            bossactive = 0;
            bossdead = 1;
        }
        return;
    }

    if (bintro)
    {
        // drop (or fly) in from above
        bintro--;
        by16 += 48;
        if (by16 > ((bfly ? SKY : GROUND) << 4))
            by16 = (bfly ? SKY : GROUND) << 4;
        bframe = BF_IDLE + ((frame >> 3) & 1);
        if (bintro == 0)
        {
            bmove = boss_moves[stage * 8];
            btimer = 0;
            if (!bfly)
                sfx(SFX_STOMP);
        }
        return;
    }

    if (herohp)
        bossMove();
    if (bghost)
        return;    // out of reach while it teleports

    // hit box
    bx = (s16)bossX();
    fy = bossFeet();
    top = fy - 50;
    feet = (s16)heroy + 31;
    if (binv)
        binv--;
    if (!binv)
    {
        dmg = shotHits(bx + 10, top, bx + 54, fy);
        // arms up: ordinary shots from the front bounce off
        if (dmg && bguard && bdir == ((s16)herox + 16 > bx + 32 ? 1 : 0) && dmg < (hero == HERO_WES ? 4 : 3))
        {
            dmg = 0;
            spawnSpark(bx + (bdir ? 48 : 0), top + 12);
            sfx(SFX_LAND);
        }
        if (dmg)
        {
            if (bhp <= dmg)
                bhp = 0;
            else
                bhp -= dmg;
            binv = 12;
            sfx(SFX_BLEAT);
        }
    }
    if (herohp && (s16)herox + 22 > bx + 12 && (s16)herox + 10 < bx + 52 && feet > top + 4 &&
        (s16)heroy + herotop < fy)
    {
        if (*heroyv > 0 && feet < top + 16 && !binv)
        {
            heroBounce((pad0 & KEY_B) ? -0x0480 : -0x0380);
            if (bhp <= 2)
                bhp = 0;
            else
                bhp -= 2;
            binv = 24;
            sfx(SFX_STOMP);
            spawnSpark(herox + 8, top - 8);
        }
        else if (!binv || *heroyv <= 0)
            heroHurt(bx + 32);
    }
    if (binv & 2)
        bframe = BF_HURT;
    if (bhp != lastbhp)
        hudBossBar();
    // half health: the angry list of moves
    if (!bangry && bhp && bhp * 2 <= boss_hp[stage])
    {
        bangry = 4;
        sfx(SFX_ROAR);
    }
    if (bhp == 0)
    {
        bdying = 120;
        sfx(SFX_ROAR);
        for (bn = 0; bn < MAX_BSHOTS; bn++)
            bshots[bn].alive = 0;
        nbshots = 0;
    }
}

void bossDraw(void)
{
    s16 sx, sy;
    u8 q, flip;
    if (!bossactive)
        return;
    // fading out to teleport: blinks, faster and faster
    if (bghost && bmove == M_TELEPORT && btimer < 30 && (btimer & (btimer < 15 ? 4 : 2)))
        return;
    sx = (s16)bossX() - (s16)x_pos;
    sy = bossFeet() - 64 - (s16)y_pos;
    flip = bdir ? 0 : 1;
    if (!(bdying && (bdying & 2)))
    {
        for (q = 0; q < 4; q++)
            drawBig(sx + (((q & 1) ^ flip) ? 32 : 0), sy + ((q & 2) ? 32 : 0), bframe * 4 + q,
                    ATTR_SPRITE(PAL_BOSS) | (flip ? 0x40 : 0), a_boss);
    }
}

void bshotsDraw(void)
{
    BShot *p = bshots;
    u8 f = SF_BSHOT + ((frame >> 3) & 1);
    for (bn = 0; bn < MAX_BSHOTS; bn++, p++)
        if (p->alive)
            drawSmall((s16)(p->x >> 4) - (s16)x_pos, (p->y >> 4) - (s16)y_pos, f,
                      ATTR_SPRITE(PAL_BOSS) | (p->vx < 0 ? 0x40 : 0), a_small);
}
