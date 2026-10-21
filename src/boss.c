/*---------------------------------------------------------------------------------

    COMRADES - the end-of-stage bosses

    Every boss is a 64x64 sprite (four 32x32 quadrants) driven by a short
    list of moves that loops: walk, charge, jump, throw in an arc, fire
    straight, and for the flyers hover, swoop and drop.

---------------------------------------------------------------------------------*/
#include "game.h"

#define M_WALK 0
#define M_CHARGE 1
#define M_JUMP 2
#define M_ARC 3
#define M_WAVE 4
#define M_HOVER 5
#define M_SWOOP 6
#define M_DROP 7

#define BF_IDLE 0
#define BF_ATTACK 2
#define BF_HURT 3
#define SF_BSHOT 11
#define GROUND 192
#define SKY 116
#define MAX_BSHOTS 6

const u8 boss_hp[6] = {16, 18, 20, 16, 22, 22};
const u8 boss_fly[6] = {0, 0, 0, 1, 0, 1};
const u8 boss_moves[24] = {
    M_WALK, M_CHARGE, M_JUMP, M_CHARGE,      // Champion Bull
    M_WAVE, M_WALK, M_WAVE, M_JUMP,          // Feedback the amp stack
    M_WALK, M_ARC, M_CHARGE, M_ARC,          // the Bouncer
    M_HOVER, M_SWOOP, M_DROP, M_SWOOP,       // Pigeon King
    M_ARC, M_JUMP, M_WALK, M_JUMP,           // the Judge
    M_SWOOP, M_WAVE, M_SWOOP, M_DROP};       // Father Time
// shots: 1 = falls under gravity
const u8 boss_shotgrav[6] = {1, 0, 1, 1, 1, 0};
char *const boss_name[6] = {"CHAMPION BULL", "FEEDBACK", "THE BOUNCER", "PIGEON KING", "THE JUDGE",
                            "FATHER TIME"};

u8 bossactive, bossdead;
u8 bhp, bmove, bstep, bdir, binv, bframe, bdying, bintro;
u16 btimer;
u16 bx16;          // left edge, 1/16 px
s16 by16;          // feet, 1/16 px
s16 bvx, bvy;      // 1/16 px per frame
u8 bfly, lastbhp;
u16 bsx[MAX_BSHOTS];
s16 bsy[MAX_BSHOTS], bsvx[MAX_BSHOTS], bsvy[MAX_BSHOTS];
u8 bsalive[MAX_BSHOTS], bsgrav[MAX_BSHOTS];
u8 bn;

void bossInit(void)
{
    bossactive = 0;
    bossdead = 0;
    bdying = 0;
    for (bn = 0; bn < MAX_BSHOTS; bn++)
        bsalive[bn] = 0;
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

void bossShot(s16 x, s16 y, s16 vx, s16 vy, u8 grav)
{
    for (bn = 0; bn < MAX_BSHOTS; bn++)
    {
        if (!bsalive[bn])
        {
            bsalive[bn] = 1;
            bsx[bn] = x << 4;
            bsy[bn] = y << 4;
            bsvx[bn] = vx;
            bsvy[bn] = vy;
            bsgrav[bn] = grav;
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
    bmove = boss_moves[stage * 4 + bstep];
    btimer = 0;
    bvx = 0;
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

void bossMove(void)
{
    s16 dx, hx, cx, fy;
    u16 left = (a_arenax + 4) << 4, right = (a_arenax + 256 - 68) << 4;
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
        }
        if (btimer > 15 && (btimer % 25) < 8)
            bframe = BF_ATTACK;
        if (btimer > 100)
            nextMove();
        break;
    case M_WAVE:
        faceHero();
        if (btimer == 20 || btimer == 50 || btimer == 80)
        {
            bframe = BF_ATTACK;
            if (bfly)
            {
                // aimed at the hero
                s16 dy = (s16)heroy + 16 - (fy - 32);
                bossShot(cx - 8, fy - 40, dx / 4, dy / 4, 0);
            }
            else
                bossShot(cx - 8 + (bdir ? 24 : -24), (btimer == 50) ? fy - 44 : fy - 14, bdir ? 48 : -48, 0, 0);
        }
        if (btimer > 15 && (btimer % 30) < 10)
            bframe = BF_ATTACK;
        if (btimer > 110)
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
    }
    if (bx16 < left)
        bx16 = left;
    if (bx16 > right)
        bx16 = right;
}

void bossUpdate(void)
{
    s16 top, feet, bx, fy;
    u8 dmg;
    u16 px;
    s16 py;

    // boss shots fly even after the boss is down
    for (bn = 0; bn < MAX_BSHOTS; bn++)
    {
        if (!bsalive[bn])
            continue;
        bsx[bn] += bsvx[bn];
        bsy[bn] += bsvy[bn];
        if (bsgrav[bn])
            bsvy[bn] += 2;
        px = bsx[bn] >> 4;
        py = bsy[bn] >> 4;
        if (px + 16 < a_arenax || px > a_arenax + 256 || py > GROUND || py < -32)
        {
            bsalive[bn] = 0;
            if (py > GROUND)
                spawnSpark(px, GROUND - 14);
            continue;
        }
        if (herohp && (s16)herox + 22 > (s16)px + 3 && (s16)herox + 10 < (s16)px + 13 &&
            (s16)heroy + 31 > py + 3 && (s16)heroy + heroyofs < py + 13)
        {
            heroHurt(px + 8);
            bsalive[bn] = 0;
        }
    }

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
            bmove = boss_moves[stage * 4];
            btimer = 0;
            if (!bfly)
                sfx(SFX_STOMP);
        }
        return;
    }

    if (herohp)
        bossMove();

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
        (s16)heroy + heroyofs < fy)
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
    if (bhp == 0)
    {
        bdying = 120;
        sfx(SFX_ROAR);
        for (bn = 0; bn < MAX_BSHOTS; bn++)
            bsalive[bn] = 0;
    }
}

void bossDraw(void)
{
    s16 sx, sy;
    u8 q, flip;
    if (bossactive)
    {
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
    for (bn = 0; bn < MAX_BSHOTS; bn++)
        if (bsalive[bn])
            drawSmall((s16)(bsx[bn] >> 4) - (s16)x_pos, (bsy[bn] >> 4) - (s16)y_pos, SF_BSHOT + ((frame >> 3) & 1),
                      ATTR_SPRITE(PAL_BOSS) | (bsvx[bn] < 0 ? 0x40 : 0), a_small);
}
