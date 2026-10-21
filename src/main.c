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

---------------------------------------------------------------------------------*/
#include <snes.h>
#include "build/stage1_objects.h"

extern char stage1_bg1_pic, stage1_bg1_pic_end, stage1_map, stage1_tiledef, stage1_tileprop, stage1_bg_pal, stage1_hero;
extern char stage1_bg2_pic, stage1_bg2_pic_end, stage1_bg2_map;
extern char logo_pic, logo_pic_end, logo_pal, title_bg1_map, font_pic, font_pic_end, ui_pal;
extern char jon_top, jon_bot, jon_pal, jon_dim_pal;
extern char wes_top, wes_bot, wes_pal, wes_dim_pal;
extern char goat_pic, small_pic, critters_pal;

#define HERO_JON 0
#define HERO_WES 1

// hero animation frames (see tools/heroes.py)
#define F_IDLE 0
#define F_RUN 2
#define F_JUMP 8
#define F_FALL 9
#define F_THROW0 10
#define F_THROW1 11
#define F_HURT 12

// sprite buffer slots
#define SPR_HERO 0
#define SPR_GOAT 2
#define SPR_GRAPE 10
#define SPR_SPARK 14

#define MAX_GRAPES 3
#define MAX_SPARKS 4
#define GROUND_Y 192
#define GOAT_Y 162

#define ATTR_SPRITE(pal) (OBJ_PRIO(2) | ((pal) << 1))

u8 hero;                       // HERO_JON or HERO_WES
u16 pad0, padpressed;

// ---------------------------------------------------------------- HUD (BG3)
u16 hud[32 * 32];
u8 huddirty;
u16 i, j;

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
        WaitForVBlank();
    }
}

void fadeOut(void)
{
    u8 b;
    for (b = 15; b > 0; b--)
    {
        setBrightness(b - 1);
        WaitForVBlank();
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

// ---------------------------------------------------------------- hero
u16 heroid;
t_objs *heroobj;
u16 *heroox, *herooy;
s16 *heroxv, *heroyv;
u16 herox, heroy;
u8 heroflip, heroframe, herolastframe, heroanim;
u8 herohp, heroinvuln, herothrow, heroground;
s16 hero_accel, hero_maxspeed, hero_jump;

// grapes and sparks use 1/16 pixel fixed point
u16 grx[MAX_GRAPES], gry[MAX_GRAPES];
s16 grvx[MAX_GRAPES], grvy[MAX_GRAPES];
u8 gralive[MAX_GRAPES], grlife[MAX_GRAPES];
u16 spx[MAX_SPARKS], spy[MAX_SPARKS];
u8 sptime[MAX_SPARKS];

// goats
u16 gtx[STAGE1_NGOATS], gtmin[STAGE1_NGOATS], gtmax[STAGE1_NGOATS];
u8 gtdir[STAGE1_NGOATS], gtstate[STAGE1_NGOATS], gthp[STAGE1_NGOATS], gttimer[STAGE1_NGOATS];
u8 gtslot[STAGE1_NGOATS], gtframe[STAGE1_NGOATS];
#define GOAT_WALK 0
#define GOAT_CHARGE 1
#define GOAT_HURT 2
#define GOAT_DEAD 3

u16 frame;
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
            grlife[j] = 90;
            if (heroflip)
            {
                grx[j] = (herox + 2) << 4;
                grvx[j] = -44;
            }
            else
            {
                grx[j] = (herox + 22) << 4;
                grvx[j] = 44;
            }
            gry[j] = (heroy + 18) << 4;
            grvy[j] = -36;
            grvx[j] += (*heroxv) >> 5;
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
    if (hero == HERO_JON)
    {
        heroobj->yofs = 16;
        heroobj->height = 47;
    }
    else
    {
        heroobj->yofs = 21;
        heroobj->height = 42;
    }
    heroox = (u16 *)&(heroobj->xpos + 1);
    herooy = (u16 *)&(heroobj->ypos + 1);
    heroxv = (s16 *)&(heroobj->xvel);
    heroyv = (s16 *)&(heroobj->yvel);
    heroobj->action = ACT_STAND;
}

void heroHurt(s16 fromx)
{
    if (heroinvuln || herohp == 0)
        return;
    herohp--;
    heroinvuln = 90;
    herothrow = 0;
    *heroyv = -0x0280;
    if (fromx > herox)
        *heroxv = -0x0200;
    else
        *heroxv = 0x0200;
}

void heroupdate(u8 idx)
{
    heroobj = &objbuffers[idx];
    pad0 = padsCurrent(0);
    padpressed = padsDown(0);

    if (stagedone)
        pad0 = 0, padpressed = 0;

    if (heroinvuln < 60)    // brief loss of control after a hit
    {
        if (pad0 & KEY_LEFT)
        {
            heroflip = 1;
            *heroxv -= hero_accel;
            if (*heroxv < -hero_maxspeed)
                *heroxv = -hero_maxspeed;
        }
        if (pad0 & KEY_RIGHT)
        {
            heroflip = 0;
            *heroxv += hero_accel;
            if (*heroxv > hero_maxspeed)
                *heroxv = hero_maxspeed;
        }
        if ((padpressed & KEY_B) && heroobj->tilestand)
            *heroyv = -hero_jump;
        if ((padpressed & KEY_Y) && herothrow == 0)
            herothrow = 18;
    }
    // short hop when B is let go early
    if (!(pad0 & KEY_B) && *heroyv < -0x0180)
        *heroyv = -0x0180;

    objCollidMap(idx);
    objUpdateXY(idx);
    heroground = heroobj->tilestand != 0;

    herox = *heroox;
    heroy = *herooy;
    if (herox < 4)
    {
        herox = 4;
        *heroox = 4;
    }

    if (herothrow)
    {
        if (herothrow == 12)
            throwGrape();
        herothrow--;
    }
    if (heroinvuln)
        heroinvuln--;

    // pick the animation frame
    heroanim++;
    if (heroinvuln > 60)
        heroframe = F_HURT;
    else if (herothrow > 12)
        heroframe = F_THROW0;
    else if (herothrow)
        heroframe = F_THROW1;
    else if (!heroground)
        heroframe = (*heroyv < 0) ? F_JUMP : F_FALL;
    else if (*heroxv > 0x40 || *heroxv < -0x40)
        heroframe = F_RUN + ((heroanim >> 2) % 6);
    else
        heroframe = F_IDLE + ((heroanim >> 5) & 1);

    mapUpdateCamera(herox, heroy);
}

// ---------------------------------------------------------------- goats
void goatsReset(void)
{
    for (i = 0; i < STAGE1_NGOATS; i++)
    {
        gtx[i] = stage1_goats[i * 3];
        gtmin[i] = stage1_goats[i * 3 + 1];
        gtmax[i] = stage1_goats[i * 3 + 2];
        gtdir[i] = 1;
        gtstate[i] = GOAT_WALK;
        gthp[i] = 2;
        gttimer[i] = 0;
        gtslot[i] = 0xFF;
    }
}

void goatsUpdate(void)
{
    s16 dx;
    for (i = 0; i < STAGE1_NGOATS; i++)
    {
        if (gtstate[i] == GOAT_DEAD)
            continue;
        // only run goats near the camera
        if (gtx[i] + 64 < x_pos || gtx[i] > x_pos + 320)
            continue;

        dx = (s16)herox - (s16)gtx[i];
        if (gtstate[i] == GOAT_WALK)
        {
            if ((frame & 1) == 0)
            {
                if (gtdir[i])
                    gtx[i]++;
                else
                    gtx[i]--;
            }
            if (gtx[i] >= gtmax[i])
                gtdir[i] = 0;
            if (gtx[i] <= gtmin[i])
                gtdir[i] = 1;
            gtframe[i] = (frame >> 4) & 1;
            // spot the hero on the ground in front: lower the horns and charge
            if (heroy > 110 && gttimer[i] == 0)
            {
                if ((gtdir[i] && dx > 0 && dx < 96) || (!gtdir[i] && dx < 0 && dx > -96))
                {
                    gtstate[i] = GOAT_CHARGE;
                    gttimer[i] = 50;
                }
            }
            if (gttimer[i])
                gttimer[i]--;
        }
        else if (gtstate[i] == GOAT_CHARGE)
        {
            gtframe[i] = 2;
            if (gttimer[i] < 40)   // short wind-up, then a fast run
            {
                if (gtdir[i] && gtx[i] < gtmax[i] + 32)
                    gtx[i] += 2;
                if (!gtdir[i] && gtx[i] > gtmin[i] - 32)
                    gtx[i] -= 2;
            }
            gttimer[i]--;
            if (gttimer[i] == 0)
            {
                gtstate[i] = GOAT_WALK;
                gttimer[i] = 60;
            }
        }
        else if (gtstate[i] == GOAT_HURT)
        {
            gtframe[i] = 3;
            if (gtdir[i])
                gtx[i]--;
            else
                gtx[i]++;
            gttimer[i]--;
            if (gttimer[i] == 0)
            {
                if (gthp[i] == 0)
                {
                    gtstate[i] = GOAT_DEAD;
                    spawnSpark(gtx[i] + 8, GOAT_Y + 8);
                }
                else
                {
                    gtstate[i] = GOAT_WALK;
                    gttimer[i] = 40;
                }
            }
        }

        // touching the hero: stomp from above, otherwise the goat wins
        if (gtstate[i] != GOAT_HURT && gtstate[i] != GOAT_DEAD)
        {
            if (herox + 22 > gtx[i] + 4 && herox + 10 < gtx[i] + 28 && heroy + 63 > GOAT_Y + 10 &&
                heroy + 20 < GOAT_Y + 30)
            {
                if (*heroyv > 0 && heroy + 63 < GOAT_Y + 18)
                {
                    *heroyv = -0x0300;
                    gthp[i] = 0;
                    gtstate[i] = GOAT_HURT;
                    gttimer[i] = 16;
                    spawnSpark(gtx[i] + 8, GOAT_Y);
                }
                else
                    heroHurt(gtx[i] + 16);
            }
        }
    }
}

void grapesUpdate(void)
{
    u16 px, py;
    for (i = 0; i < MAX_GRAPES; i++)
    {
        if (!gralive[i])
            continue;
        grx[i] += grvx[i];
        gry[i] += grvy[i];
        grvy[i] += 3;
        grlife[i]--;
        px = grx[i] >> 4;
        py = gry[i] >> 4;
        if (py > GROUND_Y - 8 || grlife[i] == 0 || px + 16 < x_pos || px > x_pos + 256)
        {
            gralive[i] = 0;
            if (py > GROUND_Y - 8)
                spawnSpark(px - 4, GROUND_Y - 16);
            continue;
        }
        for (j = 0; j < STAGE1_NGOATS; j++)
        {
            if (gtstate[j] == GOAT_DEAD || gtstate[j] == GOAT_HURT)
                continue;
            if (px + 4 > gtx[j] + 2 && px < gtx[j] + 30 && py + 4 > GOAT_Y + 4 && py < GOAT_Y + 30)
            {
                gralive[i] = 0;
                if (gthp[j])
                    gthp[j]--;
                if (hero == HERO_WES && gthp[j])   // Wes hits harder
                    gthp[j]--;
                gtstate[j] = GOAT_HURT;
                gttimer[j] = 12;
                gtdir[j] = grvx[i] < 0;
                spawnSpark(px - 6, py - 6);
                break;
            }
        }
    }
    for (i = 0; i < MAX_SPARKS; i++)
        if (sptime[i])
            sptime[i]--;
}

// ---------------------------------------------------------------- drawing
u8 slot32;

void drawHero(void)
{
    s16 sx, sy;
    u8 attr;
    sx = (s16)herox - (s16)x_pos;
    sy = (s16)heroy - (s16)y_pos;
    attr = ATTR_SPRITE(hero) | (heroflip ? 0x40 : 0);
    // blink while invulnerable
    if (heroinvuln && (heroinvuln & 4))
        sy = 240;
    oambuffer[SPR_HERO].oamx = sx;
    oambuffer[SPR_HERO].oamy = sy;
    oambuffer[SPR_HERO + 1].oamx = sx;
    oambuffer[SPR_HERO + 1].oamy = sy + 32;
    oambuffer[SPR_HERO].oamattribute = attr;
    oambuffer[SPR_HERO + 1].oamattribute = attr;
    if (heroframe != herolastframe)
    {
        oambuffer[SPR_HERO].oamframeid = heroframe;
        oambuffer[SPR_HERO + 1].oamframeid = heroframe;
        oambuffer[SPR_HERO].oamrefresh = 1;
        oambuffer[SPR_HERO + 1].oamrefresh = 1;
        herolastframe = heroframe;
    }
    oamDynamic32Draw(SPR_HERO);
    oamDynamic32Draw(SPR_HERO + 1);
    slot32 = 2;
}

void drawGoats(void)
{
    s16 sx;
    u8 n;
    for (i = 0; i < STAGE1_NGOATS; i++)
    {
        if (gtstate[i] == GOAT_DEAD)
            continue;
        sx = (s16)gtx[i] - (s16)x_pos;
        if (sx < -32 || sx > 255)
        {
            gtslot[i] = 0xFF;
            continue;
        }
        if (slot32 >= 8)
            break;
        n = SPR_GOAT + slot32 - 2;
        oambuffer[n].oamx = sx;
        oambuffer[n].oamy = GOAT_Y - (s16)y_pos;
        oambuffer[n].oamattribute = ATTR_SPRITE(2) | (gtdir[i] ? 0 : 0x40);
        if (gtslot[i] != slot32 || oambuffer[n].oamframeid != gtframe[i] || oambuffer[n].oamgraphics != &goat_pic)
        {
            oambuffer[n].oamframeid = gtframe[i];
            oambuffer[n].oamgraphics = &goat_pic;
            oambuffer[n].oamrefresh = 1;
        }
        gtslot[i] = slot32;
        oamDynamic32Draw(n);
        slot32++;
    }
}

void drawSmall(void)
{
    u8 n;
    n = SPR_GRAPE;
    for (i = 0; i < MAX_GRAPES; i++)
    {
        if (!gralive[i])
            continue;
        oambuffer[n].oamx = (s16)(grx[i] >> 4) - (s16)x_pos - 6;
        oambuffer[n].oamy = (s16)(gry[i] >> 4) - (s16)y_pos - 6;
        oambuffer[n].oamframeid = (frame >> 2) & 1;
        oambuffer[n].oamattribute = ATTR_SPRITE(2) | OBJ_SIZES;
        oambuffer[n].oamgraphics = &small_pic;
        oambuffer[n].oamrefresh = 1;
        oamDynamic16Draw(n);
        n++;
    }
    n = SPR_SPARK;
    for (i = 0; i < MAX_SPARKS; i++)
    {
        if (!sptime[i])
            continue;
        oambuffer[n].oamx = (s16)spx[i] - (s16)x_pos;
        oambuffer[n].oamy = (s16)spy[i] - (s16)y_pos;
        oambuffer[n].oamframeid = 2 + (12 - sptime[i]) / 4;
        oambuffer[n].oamattribute = ATTR_SPRITE(2) | OBJ_SIZES | OBJ_PRIO(3);
        oambuffer[n].oamgraphics = &small_pic;
        oambuffer[n].oamrefresh = 1;
        oamDynamic16Draw(n);
        n++;
    }
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

    for (i = 0; i < 2; i++)
    {
        oambuffer[SPR_HERO + i].oamgraphics = (hero == HERO_JON) ? (i ? &jon_bot : &jon_top) : (i ? &wes_bot : &wes_top);
        oambuffer[SPR_HERO + i].oamrefresh = 1;
    }
    herolastframe = 0xFF;

    if (hero == HERO_JON)
    {
        hero_accel = 0x0030;
        hero_maxspeed = 0x0150;
        hero_jump = 0x0480;
    }
    else
    {
        hero_accel = 0x0040;
        hero_maxspeed = 0x01A0;
        hero_jump = 0x03D0;
    }
    herohp = 3;
    heroinvuln = 0;
    herothrow = 0;
    heroflip = 0;
    stagedone = 0;
    for (i = 0; i < MAX_GRAPES; i++)
        gralive[i] = 0;
    for (i = 0; i < MAX_SPARKS; i++)
        sptime[i] = 0;
    goatsReset();
    objInitEngine();
    objInitFunctions(0, &heroinit, &heroupdate, NULL);
    objLoadObjects(&stage1_hero);
    mapLoad(&stage1_map, &stage1_tiledef, &stage1_tileprop);

    hudClear();
    hudText(1, 1, hero == HERO_JON ? "JON" : "WES");
    hudHearts();
    hudText(15, 1, "STAGE 1 FFA");
    hudFlush();

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
        goatsUpdate();
        grapesUpdate();

        if (herohp != lasthp)
            hudHearts();

        if (!stagedone && herox >= STAGE1_GOAL_X - 24)
        {
            stagedone = 1;
            hudText(10, 8, "STAGE CLEAR!");
            hudText(5, 10, "WES AND JON MET HERE...");
            hudText(6, 12, "THE ADVENTURE BEGINS");
        }
        if (stagedone)
        {
            endtimer++;
            if (endtimer > 300 || (endtimer > 60 && (padsDown(0) & KEY_START)))
                return 1;
        }
        if (herohp == 0)
        {
            endtimer++;
            if (endtimer == 1)
                hudText(9, 8, "OUCH! TRY AGAIN");
            if (endtimer > 120)
                return 0;
        }

        drawHero();
        drawGoats();
        drawSmall();

        oamInitDynamicSpriteEndFrame();
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
    u8 anim = 0;
    setScreenOff();
    setBrightness(0);
    oamClear(0, 0);
    loadCommonGfx();
    dmaCopyVram(&title_bg1_map, 0x6800, 64 * 32 * 2);
    bgSetScroll(0, 0, 0);
    oamInitDynamicSprite(0x0000, 0x1000, 0, 0, OBJ_SIZE16_L32);

    hudClear();
    hudText(6, 8, "A BEST FRIEND STORY");
    hudText(4, 10, "STAGE 1: FFA CONVENTION");
    hudText(6, 13, "CHOOSE YOUR COMRADE");
    hero = HERO_JON;
    titleDrawChoice();
    hudText(10, 27, "PRESS START");
    hudFlush();

    for (i = 0; i < 4; i++)
    {
        oambuffer[i].oamgraphics = (i < 2) ? (i ? &jon_bot : &jon_top) : (i == 3 ? &wes_bot : &wes_top);
        oambuffer[i].oamframeid = 0;
        oambuffer[i].oamrefresh = 1;
    }
    // dimmed palettes for the friend who is not picked
    setPalette(&jon_dim_pal, 128 + 3 * 16, 32);
    setPalette(&wes_dim_pal, 128 + 4 * 16, 32);
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
        }
        if (padpressed & (KEY_START | KEY_A | KEY_B))
            break;

        // the chosen friend runs in place, the other waits dimmed
        for (i = 0; i < 4; i++)
        {
            u8 f;
            u8 mine = (i < 2) ? (hero == HERO_JON) : (hero == HERO_WES);
            f = mine ? F_RUN + ((anim >> 2) % 6) : F_IDLE + ((anim >> 5) & 1);
            if (oambuffer[i].oamframeid != f)
            {
                oambuffer[i].oamframeid = f;
                oambuffer[i].oamrefresh = 1;
            }
            oambuffer[i].oamx = (i < 2) ? 48 : 176;
            oambuffer[i].oamy = 128 + ((i & 1) ? 32 : 0);
            oambuffer[i].oamattribute = ATTR_SPRITE(i < 2 ? (hero == HERO_JON ? 0 : 3) : (hero == HERO_WES ? 1 : 4));
            oamDynamic32Draw(i);
        }
        scroll++;
        oamInitDynamicSpriteEndFrame();
        WaitForVBlank();
        oamVramQueueUpdate();
        bgSetScroll(1, scroll >> 2, 0);
        hudFlush();
    }
    fadeOut();
}

//---------------------------------------------------------------------------------
int main(void)
{
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
