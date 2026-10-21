/*---------------------------------------------------------------------------------

    COMRADES - the platforming stages: hero, foes, shots, hearts, hazards

---------------------------------------------------------------------------------*/
#include "game.h"

extern char font_pic, font_pic_end, ui_pal;
extern char jon_pic, jon_pal, jon_dim_pal, wes_pic, wes_pal, wes_dim_pal;

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
#define B_WALK 0
#define B_CHARGE 1
#define B_HOP 2
#define B_FLY 3

#define MAX_FOES 24
#define MAX_SHOTS 4
#define MAX_SPARKS 6
#define WATER_Y 206           // feet below this: the hero is in a hazard
#define LOOK_AHEAD 44

// per stage, per kind (A, B, C): behaviour, hit points, walk divider, charge speed
const u8 foe_beh[18] = {
    B_CHARGE, B_CHARGE, B_HOP,      // goat, pig, chicken
    B_CHARGE, B_WALK, B_FLY,        // cat, walking amp, sour note
    B_CHARGE, B_WALK, B_HOP,        // punk, frat bro, rat
    B_CHARGE, B_WALK, B_FLY,        // security, hot dog mascot, pigeon
    B_CHARGE, B_WALK, B_FLY,        // floor buffer, suit of armour, bat
    B_CHARGE, B_CHARGE, B_HOP};     // golf cart, goose, bingo ball
const u8 foe_hp[18] = {2, 4, 1, 2, 4, 1, 2, 3, 1, 3, 3, 1, 3, 4, 1, 3, 2, 1};
const u8 foe_div[18] = {2, 3, 1, 1, 3, 1, 2, 2, 1, 2, 3, 1, 1, 3, 1, 1, 2, 1};
const u8 foe_rush[18] = {2, 1, 0, 3, 0, 0, 2, 0, 0, 2, 0, 0, 3, 0, 0, 3, 2, 0};

// gentle bob for flyers
const s8 bobtab[16] = {0, 2, 4, 5, 6, 5, 4, 2, 0, -2, -4, -5, -6, -5, -4, -2};

// stage names for the HUD
char *const stagehud[6] = {"1 FFA", "2 JAM", "3 BAR TOWN", "4 CHICAGO", "5 COURT", "6 GOLDEN"};

u16 i, j;

// ---------------------------------------------------------------- hero
u16 heroid;
t_objs *heroobj;
u16 *heroox, *herooy;
s16 *heroxv, *heroyv;
u16 herox, heroy;
u8 heroflip, heroframe;
u8 herohp, heroinvuln, herothrow, heroground, herowasground;
u8 coyote, jumpbuf, jumpcut, landtimer;
u16 heroanim, runphase;
s16 hero_accel, hero_maxspeed, hero_jump, fallspeed;
s16 look;
u8 heroyofs;
u8 stagedone;
u16 bossarena;
u8 startatarena;

// shots and sparks use 1/16 pixel fixed point
u16 shx[MAX_SHOTS], shy[MAX_SHOTS];
s16 shvx[MAX_SHOTS], shvy[MAX_SHOTS];
u8 shalive[MAX_SHOTS], shlife[MAX_SHOTS];
u16 spx[MAX_SPARKS], spy[MAX_SPARKS];
u8 sptime[MAX_SPARKS];

// foes
u16 fx[MAX_FOES], fy[MAX_FOES], fmin[MAX_FOES], fmax[MAX_FOES];
u8 fkind[MAX_FOES], ft[MAX_FOES], fdir[MAX_FOES], fstate[MAX_FOES], fhp[MAX_FOES], ftimer[MAX_FOES];
u8 fframe[MAX_FOES];
s16 fhop[MAX_FOES], fhopv[MAX_FOES];
u8 nfoes;
#define FOE_WALK 0
#define FOE_CHARGE 1
#define FOE_HURT 2
#define FOE_DEAD 3

u8 heartgot[6];
u8 lasthp;

void spawnSpark(u16 x, u16 y)
{
    for (j = 0; j < MAX_SPARKS; j++)
    {
        if (sptime[j] == 0)
        {
            spx[j] = x;
            spy[j] = y;
            sptime[j] = 12;
            return;
        }
    }
}

void throwOne(s16 vx, s16 vy)
{
    for (j = 0; j < MAX_SHOTS; j++)
    {
        if (shalive[j] == 0)
        {
            shalive[j] = 1;
            shlife[j] = 70;
            if (heroflip)
            {
                shx[j] = (herox + 6) << 4;
                shvx[j] = -vx;
            }
            else
            {
                shx[j] = (herox + 26) << 4;
                shvx[j] = vx;
            }
            shy[j] = (heroy + 10) << 4;
            shvy[j] = vy;
            shvx[j] += (*heroxv) >> 5;
            return;
        }
    }
}

void throwShot(void)
{
    throwOne(56, -26);
    if (dblshot[hero])
        throwOne(48, -46);    // the double shot powerup adds a high lob
    sfx(SFX_THROW);
}

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

    if (heroinvuln < 70)    // brief loss of control after a hit
    {
        if (pad0 & KEY_LEFT)
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
        if ((padpressed & KEY_Y) && herothrow == 0)
            herothrow = 18;
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
        coyote = 6;
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
        if (herothrow == 12)
            throwShot();
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
    else if (herothrow)
        heroframe = F_THROW + (herothrow > 12 ? 0 : (herothrow > 6 ? 1 : 2));
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
    nfoes = a_nfoes;
    for (i = 0; i < nfoes; i++)
    {
        fkind[i] = t[i * 5];
        ft[i] = stage * 3 + fkind[i] - 1;    // index into the behaviour tables
        fx[i] = t[i * 5 + 1];
        fy[i] = t[i * 5 + 2];
        fmin[i] = t[i * 5 + 3];
        fmax[i] = t[i * 5 + 4];
        fdir[i] = i & 1;
        fstate[i] = FOE_WALK;
        fhp[i] = foe_hp[ft[i]];
        ftimer[i] = 0;
        fhop[i] = 0;
        fhopv[i] = 0;
        fframe[i] = 0;
    }
    for (i = 0; i < 6; i++)
        heartgot[i] = 0;
}

// foe body box, relative to (fx, fy): x0, x1, height
u8 foeX0(u8 k) { return k == KIND_C ? 3 : 5; }
u8 foeX1(u8 k) { return k == KIND_C ? 13 : 27; }
u8 foeH(u8 k) { return k == KIND_C ? 12 : 22; }

void foeDamage(u8 k, u8 dmg, u8 fromleft)
{
    if (fhp[k] <= dmg)
        fhp[k] = 0;
    else
        fhp[k] -= dmg;
    fstate[k] = FOE_HURT;
    ftimer[k] = 14;
    fdir[k] = fromleft;    // knocked away from the hit
    sfx(SFX_BLEAT);
}

void foesUpdate(void)
{
    s16 dx, top, feet;
    u8 t, b, near, k;
    feet = (s16)heroy + 31;
    for (i = 0; i < nfoes; i++)
    {
        if (fstate[i] == FOE_DEAD)
            continue;
        // only run foes near the camera
        if (fx[i] + 96 < x_pos || fx[i] > x_pos + 352)
            continue;
        t = ft[i];
        b = foe_beh[t];
        k = fkind[i];
        dx = (s16)herox + 16 - ((s16)fx[i] + (k == KIND_C ? 8 : 16));
        near = feet > (s16)fy[i] - 40 && feet < (s16)fy[i] + 8;    // hero on the same floor

        if (fstate[i] == FOE_WALK)
        {
            if ((frame % foe_div[t]) == 0)
            {
                if (fdir[i])
                    fx[i]++;
                else
                    fx[i]--;
            }
            if (fx[i] >= fmax[i])
                fdir[i] = 0;
            if (fx[i] <= fmin[i])
                fdir[i] = 1;
            if (b == B_HOP)
            {
                // hop now and then, more often with the hero close by
                if (fhop[i] == 0 && fhopv[i] == 0 && ((frame + i * 23) % (dx > -64 && dx < 64 ? 40 : 90)) == 0)
                    fhopv[i] = -0x0300;
                fframe[i] = (fhop[i] < 0) ? SF_C_ALT + ((frame >> 2) & 1) : SF_C + ((frame >> 3) & 1);
            }
            else if (b == B_FLY)
            {
                fhop[i] = bobtab[(frame >> 2) & 15] - 24;
                fframe[i] = SF_C + ((frame >> 2) & 1);
                // swoop at a hero passing underneath
                if (ftimer[i] == 0 && dx > -40 && dx < 40 && feet > (s16)fy[i] - 24)
                {
                    fstate[i] = FOE_CHARGE;
                    ftimer[i] = 60;
                }
                if (ftimer[i])
                    ftimer[i]--;
            }
            else
            {
                fframe[i] = ((frame >> (foe_div[t] > 2 ? 4 : 3)) & 3);
                // spot the hero in front on the same floor: lower the head and charge
                if (b == B_CHARGE && near && ftimer[i] == 0)
                {
                    if ((fdir[i] && dx > 0 && dx < 112) || (!fdir[i] && dx < 0 && dx > -112))
                    {
                        fstate[i] = FOE_CHARGE;
                        ftimer[i] = (foe_rush[t] > 1) ? 56 : 80;
                        sfx(SFX_BLEAT);
                    }
                }
                if (ftimer[i])
                    ftimer[i]--;
            }
        }
        else if (fstate[i] == FOE_CHARGE)
        {
            if (b == B_FLY)
            {
                // dive towards the hero's height, then climb back up
                if (ftimer[i] > 30)
                {
                    if ((s16)fy[i] + fhop[i] < feet - 6)
                        fhop[i] += 2;
                    fx[i] += (dx > 0) ? 1 : -1;
                }
                else if (fhop[i] > -24)
                    fhop[i] -= 1;
                fframe[i] = SF_C_ALT + ((frame >> 1) & 1);
                ftimer[i]--;
                if (ftimer[i] == 0)
                {
                    fstate[i] = FOE_WALK;
                    ftimer[i] = 90;
                }
            }
            else
            {
                fframe[i] = 4 + ((frame >> 2) & 1);
                if (ftimer[i] < 44)   // short wind-up, then a run
                {
                    u8 step = foe_rush[t];
                    if (step == 1)
                        step = 1 + (frame & 1);
                    if (fdir[i] && fx[i] < fmax[i] + 24)
                        fx[i] += step;
                    if (!fdir[i] && fx[i] > fmin[i] - 24)
                        fx[i] -= step;
                }
                else
                    fframe[i] = 4;
                ftimer[i]--;
                if (ftimer[i] == 0)
                {
                    fstate[i] = FOE_WALK;
                    ftimer[i] = 70;
                }
            }
        }
        else if (fstate[i] == FOE_HURT)
        {
            fframe[i] = (k == KIND_C) ? SF_C_HURT : 6;
            if (fdir[i])
                fx[i]++;
            else
                fx[i]--;
            ftimer[i]--;
            if (ftimer[i] == 0)
            {
                if (fhp[i] == 0)
                {
                    fstate[i] = FOE_DEAD;
                    spawnSpark(fx[i] + (k == KIND_C ? 0 : 8), fy[i] + fhop[i] - 20);
                    continue;
                }
                fstate[i] = FOE_WALK;
                ftimer[i] = 40;
            }
        }

        if (b == B_HOP && (fhop[i] || fhopv[i]))
        {
            fhop[i] += fhopv[i] >> 8;
            fhopv[i] += 0x0030;
            if (fhop[i] >= 0)
            {
                fhop[i] = 0;
                fhopv[i] = 0;
            }
        }

        // touching the hero: stomp from above, otherwise the foe wins
        if (fstate[i] != FOE_HURT && fstate[i] != FOE_DEAD && herohp)
        {
            top = (s16)fy[i] + fhop[i] - foeH(k);
            if ((s16)herox + 22 > (s16)fx[i] + foeX0(k) && (s16)herox + 10 < (s16)fx[i] + foeX1(k) &&
                feet > top && (s16)heroy + heroyofs < (s16)fy[i] + fhop[i])
            {
                if (*heroyv > 0 && feet < top + 10)
                {
                    heroBounce((pad0 & KEY_B) ? -0x0440 : -0x0300);    // hold B for a big bounce
                    foeDamage(i, 2, dx < 0);
                    sfx(SFX_STOMP);
                    spawnSpark(fx[i] + (k == KIND_C ? 0 : 8), top - 8);
                }
                else
                    heroHurt(fx[i] + 16);
            }
        }
    }
}

// returns the damage of a hero shot overlapping the box, removing the shot
u8 shotHits(u16 x0, u16 y0, u16 x1, u16 y1)
{
    u16 px, py;
    u8 n;
    for (n = 0; n < MAX_SHOTS; n++)
    {
        if (!shalive[n])
            continue;
        px = shx[n] >> 4;
        py = shy[n] >> 4;
        if (px + 3 > x0 && px < x1 && py + 3 > y0 && py < y1)
        {
            shalive[n] = 0;
            spawnSpark(px - 8, py - 8);
            sfx(SFX_SPLAT);
            return hero == HERO_WES ? 2 : 1;    // Wes hits harder
        }
    }
    return 0;
}

void shotsUpdate(void)
{
    u16 px, py;
    u8 k, dmg;
    for (i = 0; i < MAX_SHOTS; i++)
    {
        if (!shalive[i])
            continue;
        shx[i] += shvx[i];
        shy[i] += shvy[i];
        shvy[i] += 2;
        shlife[i]--;
        px = shx[i] >> 4;
        py = shy[i] >> 4;
        if (py > 188 || py > 0x8000 || shlife[i] == 0 || px + 16 < x_pos || px > x_pos + 256)
        {
            shalive[i] = 0;
            if (py > 188 && py < 0x8000)
            {
                spawnSpark(px - 8, 178);
                sfx(SFX_SPLAT);
            }
        }
    }
    for (j = 0; j < nfoes; j++)
    {
        if (fstate[j] == FOE_DEAD || fstate[j] == FOE_HURT)
            continue;
        if (fx[j] + 32 < x_pos || fx[j] > x_pos + 256)
            continue;
        k = fkind[j];
        dmg = shotHits(fx[j] + foeX0(k), fy[j] + fhop[j] - foeH(k) - 2, fx[j] + foeX1(k), fy[j] + fhop[j]);
        if (dmg)
            foeDamage(j, dmg, fx[j] > herox);
    }
    for (i = 0; i < MAX_SPARKS; i++)
        if (sptime[i])
            sptime[i]--;
}

void heartsUpdate(void)
{
    u16 hx, hy;
    for (i = 0; i < a_nhearts; i++)
    {
        if (heartgot[i])
            continue;
        hx = a_hearttab[i * 2];
        hy = a_hearttab[i * 2 + 1];
        if (herox + 22 > hx + 2 && herox + 10 < hx + 14 && heroy + 31 > hy && heroy + heroyofs < hy + 16)
        {
            heartgot[i] = 1;
            if (herohp < hpmax[hero])
                herohp++;
            sfx(SFX_HEART);
            spawnSpark(hx, hy);
        }
    }
}

// ---------------------------------------------------------------- drawing
void drawWorld(void)
{
    s16 sx, sy;
    u8 k, attr;
    nbig = BIG_FIRST;
    nsmall = SMALL_FIRST;

    // hero (blinks while invulnerable)
    sx = (s16)herox - (s16)x_pos;
    sy = (s16)heroy - (s16)y_pos;
    if (heroinvuln && (heroinvuln & 4))
        sy = 240;
    drawBig(sx, sy, heroframe, ATTR_SPRITE(hero) | (heroflip ? 0x40 : 0), hero == HERO_JON ? &jon_pic : &wes_pic);

    bossDraw();

    for (i = 0; i < nfoes; i++)
    {
        if (fstate[i] == FOE_DEAD)
            continue;
        k = fkind[i];
        sx = (s16)fx[i] - (s16)x_pos;
        if (sx < -32 || sx > 256)
            continue;
        attr = fdir[i] ? 0 : 0x40;
        if (fstate[i] == FOE_HURT)
            attr ^= 0x40;    // still faces the hero while knocked back
        if (k == KIND_C)
            drawSmall(sx, (s16)fy[i] + fhop[i] - 16 - (s16)y_pos, fframe[i], ATTR_SPRITE(PAL_FOE_A) | attr, a_small);
        else if (k == KIND_B)
            drawBig(sx, (s16)fy[i] - 32 - (s16)y_pos, 7 + fframe[i], ATTR_SPRITE(PAL_FOE_B) | attr, a_foes);
        else
            drawBig(sx, (s16)fy[i] - 32 - (s16)y_pos, fframe[i], ATTR_SPRITE(PAL_FOE_A) | attr, a_foes);
    }

    for (i = 0; i < MAX_SHOTS; i++)
        if (shalive[i])
            drawSmall((s16)(shx[i] >> 4) - (s16)x_pos - 6, (s16)(shy[i] >> 4) - (s16)y_pos - 6,
                      SF_SHOT + ((frame >> 2) & 1), ATTR_SPRITE(PAL_FOE_A), a_small);
    for (i = 0; i < MAX_SPARKS; i++)
        if (sptime[i])
            drawSmall((s16)spx[i] - (s16)x_pos, (s16)spy[i] - (s16)y_pos, SF_SPARK + (12 - sptime[i]) / 4,
                      ATTR_SPRITE(PAL_FOE_A) | OBJ_PRIO(3), a_small);
    for (i = 0; i < a_nhearts; i++)
        if (!heartgot[i])
            drawSmall((s16)a_hearttab[i * 2] - (s16)x_pos,
                      (s16)a_hearttab[i * 2 + 1] - (s16)y_pos + (((frame >> 4) & 1) ? 1 : 0), SF_HEART,
                      ATTR_SPRITE(PAL_FOE_A), a_small);
}

void hudHearts(void)
{
    for (i = 0; i < 5; i++)
    {
        if (i < hpmax[hero])
            hud[1 * 32 + 5 + i] = (i < herohp ? 0x40 : 0x41) | 0x2000 | (1 << 10);
        else
            hud[1 * 32 + 5 + i] = 0;
    }
    huddirty = 1;
    lasthp = herohp;
}

// ---------------------------------------------------------------- stage flow
void stageStart(u8 atarena)
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
    setPalette(a_sprb, 208, 32);
    setPalette(a_bosspal, 224, 32);
    dmaCopyVram(a_bg1pic, 0x2000, a_bg1size);
    dmaCopyVram(a_bg2pic, 0x4000, a_bg2size);
    dmaCopyVram(a_bg2map, 0x7000, 64 * 32 * 2);
    dmaCopyVram(&font_pic, 0x6000, (&font_pic_end - &font_pic));
    screenSetup();
    oamInitDynamicSprite(0x0000, 0x1000, 0, 0, OBJ_SIZE16_L32);
    spritesReset();

    if (hero == HERO_JON)
    {
        // Jon: taller, floatier, jumps higher
        hero_accel = 0x0028;
        hero_maxspeed = 0x0160;
        hero_jump = 0x0410;
        heroyofs = 3;
    }
    else
    {
        // Wes: quicker on his feet, lower jump, shots hit twice as hard
        hero_accel = 0x0034;
        hero_maxspeed = 0x0190;
        hero_jump = 0x03A0;
        heroyofs = 6;
    }
    herohp = hpmax[hero];
    heroinvuln = 0;
    herothrow = 0;
    heroflip = 0;
    heroground = 0;
    coyote = 0;
    jumpbuf = 0;
    landtimer = 0;
    look = 0;
    stagedone = 0;
    startatarena = atarena;
    for (i = 0; i < MAX_SHOTS; i++)
        shalive[i] = 0;
    for (i = 0; i < MAX_SPARKS; i++)
        sptime[i] = 0;
    foesReset();
    bossInit();
    objInitEngine();
    objInitFunctions(0, &heroinit, &heroupdate, NULL);
    objLoadObjects(a_hero);
    mapLoad(a_map, a_tiledef, a_tileprop);
    if (atarena)
    {
        // retry from the arena gate
        *heroox = a_arenax - 40;
        herox = *heroox;
        for (i = 0; i < nfoes; i++)
            fstate[i] = FOE_DEAD;
    }

    hudClear();
    hudTextPal(1, 1, hero == HERO_JON ? "JON" : "WES", 2);
    hudHearts();
    hudText(20, 1, stagehud[stage]);
    hudFlush();

    playMusic(MOD_STAGE1 + stage);
    setScreenOn();
}

// returns 1 when the stage is cleared, 0 to retry (from the stage start),
// 2 to retry from the boss arena
u8 stageLoop(void)
{
    u16 endtimer = 0;
    u8 first = 1;
    while (1)
    {
        frame++;
        mapUpdate();
        objUpdateAll();
        foesUpdate();
        shotsUpdate();
        heartsUpdate();
        bossUpdate();

        if (herohp != lasthp)
            hudHearts();

        // reaching the arena wakes the boss
        if (!bossactive && !bossdead && herox >= a_arenax + 40)
            bossStart();

        if (bossdead && !stagedone)
        {
            stagedone = 1;
            playMusic(MOD_CLEAR);
            hudTextPal(10, 8, "STAGE CLEAR!", 2);
        }
        if (stagedone)
        {
            endtimer++;
            if (endtimer > 330 || (endtimer > 60 && (padsDown(0) & KEY_START)))
                return 1;
        }
        if (herohp == 0)
        {
            endtimer++;
            if (endtimer == 1)
            {
                spcStop();
                hudTextPal(9, 8, "OUCH! TRY AGAIN", 2);
            }
            if (endtimer > 120)
                return bossactive ? 2 : 0;
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
