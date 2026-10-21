/*---------------------------------------------------------------------------------

    COMRADES - a best friend adventure through the stages of life
    Stage 1: the FFA Convention

    VRAM map (word addresses)
      0x0000  large (32x32) dynamic sprite graphics
      0x1000  small (16x16) dynamic sprite graphics
      0x2000  BG1 tiles (stage tiles, title logo from tile 256)
      0x4000  BG2 tiles (hall backdrop)
      0x6000  BG3 tiles (2bpp font + HUD icons)
      0x6800  BG1 map 64x32 (map engine)
      0x7000  BG2 map 64x32
      0x7800  BG3 map 32x32 (HUD / text)

    Sprite palettes: 0 Jon, 1 Wes, 2 critters, 3/4 dimmed Jon/Wes (title), 5 pig

---------------------------------------------------------------------------------*/
#include <snes.h>
#include "build/stage1_objects.h"
#include "build/soundbank.h"
#include "build/sfx.h"

extern char SOUNDBANK__;
extern char stage1_bg1_pic, stage1_bg1_pic_end, stage1_map, stage1_tiledef, stage1_tileprop, stage1_bg_pal, stage1_hero;
extern char stage1_bg2_pic, stage1_bg2_pic_end, stage1_bg2_map;
extern char logo_pic, logo_pic_end, logo_pal, title_bg1_map, font_pic, font_pic_end, ui_pal;
extern char jon_pic, jon_pal, jon_dim_pal;
extern char wes_pic, wes_pal, wes_dim_pal;
extern char beasts_pic, small_pic, critters_pal, pig_pal;

#define HERO_JON 0
#define HERO_WES 1

// hero animation frames (see tools/heroes.py)
#define F_IDLE 0
#define F_RUN 4
#define F_JUMP 12
#define F_APEX 13
#define F_FALL 14
#define F_LAND 15
#define F_THROW 16
#define F_HURT 19
#define F_CHEER 20

// beasts.png frames: goat 0-6, pig 7-13 (walk0-3, charge0-1, hurt)
#define BF_WALK 0
#define BF_CHARGE 4
#define BF_HURT 6
#define BF_PIG 7
// small.png frames
#define SF_GRAPE 0
#define SF_SPARK 2
#define SF_HEART 5
#define SF_CHICK 6
#define SF_CHICK_FLAP 8
#define SF_CHICK_HURT 10

// object types (match tools/ffa_stage.py)
#define OBJ_GOAT 1
#define OBJ_PIG 3
#define OBJ_CHICKEN 4

#define MAX_GRAPES 3
#define MAX_SPARKS 4
#define GROUND_Y 192
#define WATER_Y 206          // feet below this means the hero is in a trough
#define LOOK_AHEAD 44

#define ATTR_SPRITE(pal) (OBJ_PRIO(2) | ((pal) << 1))
#define PAL_CRITTER 2
#define PAL_PIG 5

u8 hero;                       // HERO_JON or HERO_WES
u16 pad0, padpressed;
u16 i, j;
u16 frame;

// ---------------------------------------------------------------- frame pacing
void waitFrame(void)
{
    spcProcess();
    WaitForVBlank();
}

void sfx(u8 id)
{
    spcEffect(4, id, 15 * 16 + 8);
}

void playMusic(u8 mod)
{
    spcStop();
    spcLoad(mod);
    for (i = 0; i < SFX_COUNT; i++)
        spcLoadEffect(i);
    spcPlay(0);
}

// ---------------------------------------------------------------- HUD (BG3)
u16 hud[32 * 32];
u8 huddirty;

void hudClear(void)
{
    for (i = 0; i < 32 * 32; i++)
        hud[i] = 0;
    huddirty = 1;
}

void hudText(u16 x, u16 y, char *s)
{
    u16 p = y * 32 + x;
    while (*s)
    {
        hud[p] = ((*s) - 0x20) | 0x2000;
        p++;
        s++;
    }
    huddirty = 1;
}

void hudClearRow(u16 y)
{
    for (i = 0; i < 32; i++)
        hud[y * 32 + i] = 0;
    huddirty = 1;
}

void hudFlush(void)
{
    if (huddirty)
    {
        dmaCopyVram((u8 *)hud, 0x7800, 32 * 32 * 2);
        huddirty = 0;
    }
}

// ---------------------------------------------------------------- screen helpers
void fadeIn(void)
{
    u8 b;
    for (b = 1; b <= 15; b++)
    {
        setBrightness(b);
        waitFrame();
    }
}

void fadeOut(void)
{
    u8 b;
    for (b = 15; b > 0; b--)
    {
        setBrightness(b - 1);
        waitFrame();
    }
}

void loadCommonGfx(void)
{
    // BG palettes 0-7, then UI colours (CGRAM 0-15) and the logo palette (BG palette 3)
    setPalette(&stage1_bg_pal, 0, 256);
    setPalette(&ui_pal, 0, 32);
    setPalette(&logo_pal, 48, 32);
    setPalette(&jon_pal, 128, 32);
    setPalette(&wes_pal, 144, 32);
    setPalette(&critters_pal, 160, 32);
    setPalette(&jon_dim_pal, 176, 32);
    setPalette(&wes_dim_pal, 192, 32);
    setPalette(&pig_pal, 208, 32);

    dmaCopyVram(&stage1_bg1_pic, 0x2000, (&stage1_bg1_pic_end - &stage1_bg1_pic));
    dmaCopyVram(&logo_pic, 0x3000, (&logo_pic_end - &logo_pic));
    dmaCopyVram(&stage1_bg2_pic, 0x4000, (&stage1_bg2_pic_end - &stage1_bg2_pic));
    dmaCopyVram(&stage1_bg2_map, 0x7000, 64 * 32 * 2);
    dmaCopyVram(&font_pic, 0x6000, (&font_pic_end - &font_pic));

    bgSetGfxPtr(0, 0x2000);
    bgSetMapPtr(0, 0x6800, SC_64x32);
    bgSetGfxPtr(1, 0x4000);
    bgSetMapPtr(1, 0x7000, SC_64x32);
    bgSetGfxPtr(2, 0x6000);
    bgSetMapPtr(2, 0x7800, SC_32x32);
    setMode(BG_MODE1, BG3_MODE1_PRIORITY_HIGH);
    bgSetEnable(0);
    bgSetEnable(1);
    bgSetEnable(2);
}

// ---------------------------------------------------------------- sprite drawing
// Dynamic sprite VRAM slots are handed out in draw order, so large sprites
// always use oambuffer[0..7] and small ones oambuffer[8..31] in the order they
// are drawn: entry n then always owns the same VRAM slot and only needs a
// re-upload when what it shows changes.
#define BIG_FIRST 0
#define BIG_LAST 7
#define SMALL_FIRST 8
#define SMALL_LAST 31
u8 nbig, nsmall;

void spritesReset(void)
{
    for (i = 0; i <= SMALL_LAST; i++)
    {
        oambuffer[i].oamgraphics = 0;
        oambuffer[i].oamframeid = 0xFF;
    }
}

void spriteSet(u8 n, s16 x, s16 y, u8 f, u8 attr, char *gfx)
{
    oambuffer[n].oamx = x;
    oambuffer[n].oamy = y;
    oambuffer[n].oamattribute = attr;
    if (oambuffer[n].oamframeid != f || oambuffer[n].oamgraphics != gfx)
    {
        oambuffer[n].oamframeid = f;
        oambuffer[n].oamgraphics = gfx;
        oambuffer[n].oamrefresh = 1;
    }
}

void drawBig(s16 x, s16 y, u8 f, u8 attr, char *gfx)
{
    if (nbig > BIG_LAST || x < -32 || x > 255 || y < -32 || y > 224)
        return;
    spriteSet(nbig, x, y, f, attr, gfx);
    oamDynamic32Draw(nbig);
    nbig++;
}

void drawSmall(s16 x, s16 y, u8 f, u8 attr)
{
    if (nsmall > SMALL_LAST || x < -16 || x > 255 || y < -16 || y > 224)
        return;
    spriteSet(nsmall, x, y, f, attr | OBJ_SIZES, &small_pic);
    oamDynamic16Draw(nsmall);
    nsmall++;
}

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

// grapes and sparks use 1/16 pixel fixed point
u16 grx[MAX_GRAPES], gry[MAX_GRAPES];
s16 grvx[MAX_GRAPES], grvy[MAX_GRAPES];
u8 gralive[MAX_GRAPES], grlife[MAX_GRAPES];
u16 spx[MAX_SPARKS], spy[MAX_SPARKS];
u8 sptime[MAX_SPARKS];

// foes: goats, pigs and chickens
u16 fx[STAGE1_NFOES], fy[STAGE1_NFOES], fmin[STAGE1_NFOES], fmax[STAGE1_NFOES];
u8 ftype[STAGE1_NFOES], fdir[STAGE1_NFOES], fstate[STAGE1_NFOES], fhp[STAGE1_NFOES], ftimer[STAGE1_NFOES];
u8 fframe[STAGE1_NFOES];
s16 fhop[STAGE1_NFOES], fhopv[STAGE1_NFOES];
#define FOE_WALK 0
#define FOE_CHARGE 1
#define FOE_HURT 2
#define FOE_DEAD 3

u8 heartgot[STAGE1_NHEARTS];
u8 stagedone;

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

void throwGrape(void)
{
    for (j = 0; j < MAX_GRAPES; j++)
    {
        if (gralive[j] == 0)
        {
            gralive[j] = 1;
            grlife[j] = 70;
            if (heroflip)
            {
                grx[j] = (herox + 6) << 4;
                grvx[j] = -56;
            }
            else
            {
                grx[j] = (herox + 26) << 4;
                grvx[j] = 56;
            }
            gry[j] = (heroy + 10) << 4;
            grvy[j] = -26;
            grvx[j] += (*heroxv) >> 5;
            sfx(SFX_THROW);
            return;
        }
    }
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

    // fell into a water trough: splash and spring back out
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
            throwGrape();
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
    mapUpdateCamera(speed, heroy);
}

// ---------------------------------------------------------------- foes
void foesReset(void)
{
    for (i = 0; i < STAGE1_NFOES; i++)
    {
        ftype[i] = stage1_foes[i * 5];
        fx[i] = stage1_foes[i * 5 + 1];
        fy[i] = stage1_foes[i * 5 + 2];
        fmin[i] = stage1_foes[i * 5 + 3];
        fmax[i] = stage1_foes[i * 5 + 4];
        fdir[i] = i & 1;
        fstate[i] = FOE_WALK;
        fhp[i] = (ftype[i] == OBJ_PIG) ? 4 : (ftype[i] == OBJ_GOAT ? 2 : 1);
        ftimer[i] = 0;
        fhop[i] = 0;
        fhopv[i] = 0;
    }
    for (i = 0; i < STAGE1_NHEARTS; i++)
        heartgot[i] = 0;
}

// foe body box, relative to (fx, fy): x0, x1, height
u8 foeX0(u8 t) { return t == OBJ_CHICKEN ? 3 : 4; }
u8 foeX1(u8 t) { return t == OBJ_CHICKEN ? 13 : 28; }
u8 foeH(u8 t) { return t == OBJ_CHICKEN ? 11 : (t == OBJ_PIG ? 15 : 14); }

void foeDamage(u8 k, u8 dmg, u8 fromleft)
{
    if (fhp[k] <= dmg)
        fhp[k] = 0;
    else
        fhp[k] -= dmg;
    fstate[k] = FOE_HURT;
    ftimer[k] = 14;
    fdir[k] = fromleft;    // knocked away from the hit
    if (ftype[k] != OBJ_CHICKEN)
        sfx(SFX_BLEAT);
}

void foesUpdate(void)
{
    s16 dx, top, feet;
    u8 t, near;
    feet = (s16)heroy + 31;
    for (i = 0; i < STAGE1_NFOES; i++)
    {
        if (fstate[i] == FOE_DEAD)
            continue;
        // only run foes near the camera
        if (fx[i] + 96 < x_pos || fx[i] > x_pos + 352)
            continue;
        t = ftype[i];
        dx = (s16)herox + 16 - ((s16)fx[i] + 16);
        near = feet > (s16)fy[i] - 40 && feet < (s16)fy[i] + 8;    // hero on the same floor

        if (fstate[i] == FOE_WALK)
        {
            // goats amble every other frame, pigs plod, chickens scurry
            if ((t == OBJ_CHICKEN) || (t == OBJ_GOAT && (frame & 1)) || (t == OBJ_PIG && (frame % 3) == 0))
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
            if (t == OBJ_CHICKEN)
            {
                // hop and flap now and then, more often with the hero close by
                if (fhop[i] == 0 && fhopv[i] == 0 && ((frame + i * 23) % (dx > -64 && dx < 64 ? 40 : 90)) == 0)
                    fhopv[i] = -0x0300;
                fframe[i] = (fhop[i] < 0) ? SF_CHICK_FLAP + ((frame >> 2) & 1) : SF_CHICK + ((frame >> 3) & 1);
            }
            else
            {
                fframe[i] = BF_WALK + ((frame >> (t == OBJ_PIG ? 4 : 3)) & 3);
                // spot the hero in front on the same floor: lower the head and charge
                if (near && ftimer[i] == 0)
                {
                    if ((fdir[i] && dx > 0 && dx < 112) || (!fdir[i] && dx < 0 && dx > -112))
                    {
                        fstate[i] = FOE_CHARGE;
                        ftimer[i] = (t == OBJ_PIG) ? 80 : 56;
                        sfx(SFX_BLEAT);
                    }
                }
                if (ftimer[i])
                    ftimer[i]--;
            }
        }
        else if (fstate[i] == FOE_CHARGE)
        {
            fframe[i] = BF_CHARGE + ((frame >> 2) & 1);
            if (ftimer[i] < 44)   // short wind-up, then a run
            {
                u8 step = (t == OBJ_PIG) ? 1 + (frame & 1) : 2;
                if (fdir[i] && fx[i] < fmax[i] + 24)
                    fx[i] += step;
                if (!fdir[i] && fx[i] > fmin[i] - 24)
                    fx[i] -= step;
            }
            else
                fframe[i] = BF_CHARGE;
            ftimer[i]--;
            if (ftimer[i] == 0)
            {
                fstate[i] = FOE_WALK;
                ftimer[i] = 70;
            }
        }
        else if (fstate[i] == FOE_HURT)
        {
            fframe[i] = (t == OBJ_CHICKEN) ? SF_CHICK_HURT : BF_HURT;
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
                    spawnSpark(fx[i] + (t == OBJ_CHICKEN ? 0 : 8), fy[i] - 20);
                    continue;
                }
                fstate[i] = FOE_WALK;
                ftimer[i] = 40;
            }
        }

        if (t == OBJ_CHICKEN && (fhop[i] || fhopv[i]))
        {
            fhop[i] += fhopv[i] >> 8;
            fhopv[i] += 0x0030;
            if (fhop[i] >= 0)
            {
                fhop[i] = 0;
                fhopv[i] = 0;
            }
        }

        // touching the hero: stomp from above, otherwise the critter wins
        if (fstate[i] != FOE_HURT && fstate[i] != FOE_DEAD && herohp)
        {
            top = (s16)fy[i] + fhop[i] - foeH(t);
            if ((s16)herox + 22 > (s16)fx[i] + foeX0(t) && (s16)herox + 10 < (s16)fx[i] + foeX1(t) &&
                feet > top && (s16)heroy + heroyofs < (s16)fy[i] + fhop[i])
            {
                if (*heroyv > 0 && feet < top + 10)
                {
                    *heroyv = (pad0 & KEY_B) ? -0x0440 : -0x0300;    // hold B for a big bounce
                    jumpcut = 1;
                    coyote = 0;
                    foeDamage(i, 2, dx < 0);
                    sfx(SFX_STOMP);
                    spawnSpark(fx[i] + (t == OBJ_CHICKEN ? 0 : 8), top - 8);
                }
                else
                    heroHurt(fx[i] + 16);
            }
        }
    }
}

void grapesUpdate(void)
{
    u16 px, py;
    u8 t;
    for (i = 0; i < MAX_GRAPES; i++)
    {
        if (!gralive[i])
            continue;
        grx[i] += grvx[i];
        gry[i] += grvy[i];
        grvy[i] += 2;
        grlife[i]--;
        px = grx[i] >> 4;
        py = gry[i] >> 4;
        if (py > GROUND_Y - 4 || grlife[i] == 0 || px + 16 < x_pos || px > x_pos + 256)
        {
            gralive[i] = 0;
            if (py > GROUND_Y - 4)
            {
                spawnSpark(px - 8, GROUND_Y - 14);
                sfx(SFX_SPLAT);
            }
            continue;
        }
        for (j = 0; j < STAGE1_NFOES; j++)
        {
            if (fstate[j] == FOE_DEAD || fstate[j] == FOE_HURT)
                continue;
            t = ftype[j];
            if (px + 3 > fx[j] + foeX0(t) && px < fx[j] + foeX1(t) && py + 3 > fy[j] + fhop[j] - foeH(t) - 2 &&
                py < fy[j] + fhop[j])
            {
                gralive[i] = 0;
                foeDamage(j, hero == HERO_WES ? 2 : 1, grvx[i] > 0);   // Wes hits harder
                sfx(SFX_SPLAT);
                spawnSpark(px - 8, py - 8);
                break;
            }
        }
    }
    for (i = 0; i < MAX_SPARKS; i++)
        if (sptime[i])
            sptime[i]--;
}

void heartsUpdate(void)
{
    u16 hx, hy;
    for (i = 0; i < STAGE1_NHEARTS; i++)
    {
        if (heartgot[i])
            continue;
        hx = stage1_hearts[i * 2];
        hy = stage1_hearts[i * 2 + 1];
        if (herox + 22 > hx + 2 && herox + 10 < hx + 14 && heroy + 31 > hy && heroy + heroyofs < hy + 16)
        {
            heartgot[i] = 1;
            if (herohp < 3)
                herohp++;
            sfx(SFX_STOMP);
            spawnSpark(hx, hy);
        }
    }
}

// ---------------------------------------------------------------- drawing
void drawWorld(void)
{
    s16 sx, sy;
    u8 t, attr;
    nbig = BIG_FIRST;
    nsmall = SMALL_FIRST;

    // hero (blinks while invulnerable)
    sx = (s16)herox - (s16)x_pos;
    sy = (s16)heroy - (s16)y_pos;
    if (heroinvuln && (heroinvuln & 4))
        sy = 240;
    drawBig(sx, sy, heroframe, ATTR_SPRITE(hero) | (heroflip ? 0x40 : 0), hero == HERO_JON ? &jon_pic : &wes_pic);

    for (i = 0; i < STAGE1_NFOES; i++)
    {
        if (fstate[i] == FOE_DEAD)
            continue;
        t = ftype[i];
        sx = (s16)fx[i] - (s16)x_pos;
        attr = fdir[i] ? 0 : 0x40;
        if (fstate[i] == FOE_HURT)
            attr ^= 0x40;    // still faces the hero while knocked back
        if (t == OBJ_CHICKEN)
            drawSmall(sx, (s16)fy[i] + fhop[i] - 16 - (s16)y_pos, fframe[i], ATTR_SPRITE(PAL_CRITTER) | attr);
        else if (t == OBJ_PIG)
            drawBig(sx, (s16)fy[i] - 32 - (s16)y_pos, BF_PIG + fframe[i], ATTR_SPRITE(PAL_PIG) | attr, &beasts_pic);
        else
            drawBig(sx, (s16)fy[i] - 32 - (s16)y_pos, fframe[i], ATTR_SPRITE(PAL_CRITTER) | attr, &beasts_pic);
    }

    for (i = 0; i < MAX_GRAPES; i++)
        if (gralive[i])
            drawSmall((s16)(grx[i] >> 4) - (s16)x_pos - 6, (s16)(gry[i] >> 4) - (s16)y_pos - 6,
                      SF_GRAPE + ((frame >> 2) & 1), ATTR_SPRITE(PAL_CRITTER));
    for (i = 0; i < MAX_SPARKS; i++)
        if (sptime[i])
            drawSmall((s16)spx[i] - (s16)x_pos, (s16)spy[i] - (s16)y_pos, SF_SPARK + (12 - sptime[i]) / 4,
                      ATTR_SPRITE(PAL_CRITTER) | OBJ_PRIO(3));
    for (i = 0; i < STAGE1_NHEARTS; i++)
        if (!heartgot[i])
            drawSmall((s16)stage1_hearts[i * 2] - (s16)x_pos,
                      (s16)stage1_hearts[i * 2 + 1] - (s16)y_pos + (((frame >> 4) & 1) ? 1 : 0), SF_HEART,
                      ATTR_SPRITE(PAL_CRITTER));
}

u8 lasthp;

void hudHearts(void)
{
    for (i = 0; i < 3; i++)
        hud[1 * 32 + 6 + i] = (i < herohp ? 0x40 : 0x41) | 0x2000 | (1 << 10);
    huddirty = 1;
    lasthp = herohp;
}

// ---------------------------------------------------------------- stage
void stageStart(void)
{
    setScreenOff();
    setBrightness(0);

    oamClear(0, 0);
    loadCommonGfx();
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
        // Wes: quicker on his feet, lower jump, grapes hit twice as hard
        hero_accel = 0x0034;
        hero_maxspeed = 0x0190;
        hero_jump = 0x03A0;
        heroyofs = 6;
    }
    herohp = 3;
    heroinvuln = 0;
    herothrow = 0;
    heroflip = 0;
    heroground = 0;
    coyote = 0;
    jumpbuf = 0;
    landtimer = 0;
    look = 0;
    stagedone = 0;
    for (i = 0; i < MAX_GRAPES; i++)
        gralive[i] = 0;
    for (i = 0; i < MAX_SPARKS; i++)
        sptime[i] = 0;
    foesReset();
    objInitEngine();
    objInitFunctions(0, &heroinit, &heroupdate, NULL);
    objLoadObjects(&stage1_hero);
    mapLoad(&stage1_map, &stage1_tiledef, &stage1_tileprop);

    hudClear();
    hudText(1, 1, hero == HERO_JON ? "JON" : "WES");
    hudHearts();
    hudText(15, 1, "STAGE 1 FFA");
    hudFlush();

    playMusic(MOD_STAGE1);
    setScreenOn();
    fadeIn();
}

// returns 1 when the stage is cleared, 0 to retry
u8 stageLoop(void)
{
    u16 endtimer = 0;
    while (1)
    {
        frame++;
        mapUpdate();
        objUpdateAll();
        foesUpdate();
        grapesUpdate();
        heartsUpdate();

        if (herohp != lasthp)
            hudHearts();

        if (!stagedone && herox >= STAGE1_GOAL_X - 24)
        {
            stagedone = 1;
            playMusic(MOD_CLEAR);
            hudText(10, 8, "STAGE CLEAR!");
            hudText(5, 10, "WES AND JON MET HERE...");
            hudText(6, 12, "THE ADVENTURE BEGINS");
        }
        if (stagedone)
        {
            endtimer++;
            if (endtimer > 360 || (endtimer > 60 && (padsDown(0) & KEY_START)))
                return 1;
        }
        if (herohp == 0)
        {
            endtimer++;
            if (endtimer == 1)
            {
                spcStop();
                hudText(9, 8, "OUCH! TRY AGAIN");
            }
            if (endtimer > 120)
                return 0;
        }

        drawWorld();

        oamInitDynamicSpriteEndFrame();
        spcProcess();
        WaitForVBlank();
        mapVblank();
        oamVramQueueUpdate();
        bgSetScroll(1, x_pos >> 1, 0);
        hudFlush();
    }
}

// ---------------------------------------------------------------- title
void titleDrawChoice(void)
{
    hudClearRow(15);
    hudClearRow(25);
    hudText(7, 15, "JON");
    hudText(21, 15, "WES");
    hudText(hero == HERO_JON ? 5 : 19, 15, ">");
    hudText(hero == HERO_JON ? 3 : 17, 25, hero == HERO_JON ? "HIGH JUMP" : "HITS HARDER");
}

void titleScreen(void)
{
    u16 scroll = 0;
    u8 anim = 0, f, mine;
    setScreenOff();
    setBrightness(0);
    oamClear(0, 0);
    loadCommonGfx();
    dmaCopyVram(&title_bg1_map, 0x6800, 64 * 32 * 2);
    bgSetScroll(0, 0, 0);
    oamInitDynamicSprite(0x0000, 0x1000, 0, 0, OBJ_SIZE16_L32);
    spritesReset();

    hudClear();
    hudText(6, 8, "A BEST FRIEND STORY");
    hudText(4, 10, "STAGE 1: FFA CONVENTION");
    hudText(6, 13, "CHOOSE YOUR COMRADE");
    hero = HERO_JON;
    titleDrawChoice();
    hudText(10, 27, "PRESS START");
    hudFlush();

    playMusic(MOD_TITLE);
    setScreenOn();
    fadeIn();

    while (1)
    {
        anim++;
        padpressed = padsDown(0);
        if (padpressed & (KEY_LEFT | KEY_RIGHT | KEY_SELECT))
        {
            hero ^= 1;
            titleDrawChoice();
            sfx(SFX_LAND);
        }
        if (padpressed & (KEY_START | KEY_A | KEY_B))
        {
            sfx(SFX_JUMP);
            break;
        }

        // the chosen friend runs in place, the other waits dimmed
        nbig = BIG_FIRST;
        nsmall = SMALL_FIRST;
        for (i = 0; i < 2; i++)
        {
            mine = (i == hero);
            f = mine ? F_RUN + ((anim >> 2) & 7) : F_IDLE + ((anim >> 4) & 3);
            drawBig(i ? 176 : 48, 160, f, ATTR_SPRITE(mine ? i : 3 + i), i ? &wes_pic : &jon_pic);
        }
        scroll++;
        oamInitDynamicSpriteEndFrame();
        waitFrame();
        oamVramQueueUpdate();
        bgSetScroll(1, scroll >> 2, 0);
        hudFlush();
    }
    // let the start sound play out while fading
    fadeOut();
}

//---------------------------------------------------------------------------------
int main(void)
{
    spcBoot();
    spcSetBank(&SOUNDBANK__);
    consoleInit();
    while (1)
    {
        titleScreen();
        while (1)
        {
            stageStart();
            if (stageLoop())
                break;
            fadeOut();
        }
        fadeOut();
    }
    return 0;
}
