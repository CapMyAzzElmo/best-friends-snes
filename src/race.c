/*---------------------------------------------------------------------------------

    COMRADES - bonus round: Road Ride

    Jon's black Suzuki B-King and Wes's red Honda RC51 race down the coast
    highway to the diner. Up/Down change lanes, B opens the throttle. Cones
    and traffic knock you down, oil spins you out, arrows give a boost.
    Win the race and the rider earns an extra heart.

---------------------------------------------------------------------------------*/
#include "game.h"

extern char race_big, race_small, jonbike_pal, wesbike_pal, bonus_obj_pal;
extern char race_bg1_pic, race_bg1_pic_end, race_bg1_map, race_bg2_pic, race_bg2_pic_end, race_bg2_map, race_bg_pal;
extern char font_pic, font_pic_end, ui_pal;

#define RACE_LEN 9600
#define LANE_TOP 146
#define LANE_BOT 206
#define PLAYER_SX 40

// big sheet frames
#define RB_JON 0
#define RB_WES 8
#define RB_CAR 16
#define RB_OIL 20
#define RB_BOOST 21
#define RB_FLAG 22
#define RF_RIDE 0
#define RF_BOOST 4
#define RF_CRASH 6

#define O_CONE 0
#define O_OIL 1
#define O_CAR 2
#define O_BOOST 3

// obstacles: distance, lane (0-2), type
const u16 course[] = {
    700, 1, O_CONE, 900, 0, O_CONE, 1100, 2, O_BOOST, 1300, 1, O_OIL, 1500, 2, O_CAR,
    1800, 0, O_CONE, 1820, 1, O_CONE, 2100, 2, O_CONE, 2300, 0, O_CAR, 2500, 1, O_BOOST,
    2700, 2, O_OIL, 2900, 1, O_CONE, 2920, 2, O_CONE, 3200, 0, O_OIL, 3400, 1, O_CAR,
    3700, 2, O_CAR, 3900, 0, O_BOOST, 4100, 1, O_CONE, 4120, 0, O_CONE, 4400, 2, O_OIL,
    4600, 1, O_CAR, 4800, 0, O_CONE, 5000, 2, O_BOOST, 5200, 1, O_OIL, 5400, 0, O_CAR,
    5600, 2, O_CONE, 5620, 1, O_CONE, 5900, 0, O_OIL, 6100, 2, O_CAR, 6300, 1, O_BOOST,
    6500, 0, O_CONE, 6700, 1, O_CAR, 6900, 2, O_OIL, 7100, 0, O_CONE, 7120, 1, O_CONE,
    7400, 2, O_CAR, 7600, 1, O_BOOST, 7800, 0, O_OIL, 8000, 2, O_CONE, 8020, 1, O_CONE,
    8300, 0, O_CAR, 8600, 1, O_OIL, 8800, 2, O_BOOST, 9100, 0, O_CONE, 9120, 2, O_CONE,
    0xFFFF};
#define NOBS 45

u16 ob_x[NOBS];
u8 ob_hit[NOBS];
u16 pdist, pfrac, rdist, rfrac;
s16 pspeed, rspeed, py, ry;
u8 pcrash, pspin, pboost, rlane, rcrash;
u16 rtimer;

s16 laneY(u8 lane)
{
    return 152 + lane * 25;
}

void raceHud(void)
{
    u8 k, pj, pr;
    hudClearRow(2);
    for (k = 0; k < 24; k++)
        hud[2 * 32 + 4 + k] = ('-' - 0x20) | 0x2000;
    pj = (pdist >= RACE_LEN) ? 23 : pdist / (RACE_LEN / 23);
    pr = (rdist >= RACE_LEN) ? 23 : rdist / (RACE_LEN / 23);
    hud[2 * 32 + 4 + pr] = ((hero == HERO_JON ? 'W' : 'J') - 0x20) | 0x2000;
    hud[2 * 32 + 4 + pj] = ((hero == HERO_JON ? 'J' : 'W') - 0x20) | 0x2000 | (2 << 10);
    hud[2 * 32 + 28] = ('#' - 0x20) | 0x2000;
    huddirty = 1;
}

void raceDrawBike(u8 who, s16 sx, s16 y, u8 f)
{
    u8 base = who == HERO_JON ? RB_JON : RB_WES;
    u8 pal = who == HERO_JON ? 3 : 4;
    if (sx < -64 || sx > 256)
        return;
    drawBig(sx, y - 32, base + f, ATTR_SPRITE(pal), &race_big);
    drawBig(sx + 32, y - 32, base + f + 1, ATTR_SPRITE(pal), &race_big);
}

u8 raceRun(void)
{
    u16 i, endtimer = 0;
    s16 sx, oy;
    u8 f, finished = 0, won = 0, t, rival;
    u16 scroll2 = 0;

    setScreenOff();
    setBrightness(0);
    oamClear(0, 0);
    setPalette(&race_bg_pal, 0, 256);
    setPalette(&ui_pal, 0, 24);
    setPalette(&race_bg_pal, 0, 2);
    setPalette(&jonbike_pal, 128 + 3 * 16, 32);
    setPalette(&wesbike_pal, 128 + 4 * 16, 32);
    setPalette(&bonus_obj_pal, 128 + 7 * 16, 32);
    dmaCopyVram(&race_bg1_pic, 0x2000, &race_bg1_pic_end - &race_bg1_pic);
    dmaCopyVram(&race_bg2_pic, 0x4000, &race_bg2_pic_end - &race_bg2_pic);
    dmaCopyVram(&race_bg1_map, 0x6800, 64 * 32 * 2);
    dmaCopyVram(&race_bg2_map, 0x7000, 64 * 32 * 2);
    dmaCopyVram(&font_pic, 0x6000, (&font_pic_end - &font_pic));
    screenSetup();
    bgSetScroll(0, 0, 0);
    bgSetScroll(1, 0, 0);
    oamInitDynamicSprite(0x0000, 0x1000, 0, 0, OBJ_SIZE16_L32);
    spritesReset();

    rival = hero ^ 1;
    for (i = 0; i < NOBS; i++)
    {
        ob_x[i] = course[i * 3];
        ob_hit[i] = 0;
    }
    pdist = 0;
    rdist = 0;
    pfrac = rfrac = 0;
    pspeed = 0;
    rspeed = 0;
    py = laneY(1);
    rlane = 0;
    ry = laneY(0);
    pcrash = pspin = pboost = rcrash = 0;
    rtimer = 0;

    hudClear();
    hudTextPal(1, 1, "ROAD RIDE", 2);
    hudText(13, 1, "RACE TO THE DINER!");
    hudText(1, 2, "GO");
    raceHud();
    hudText(9, 12, "READY...");
    hudFlush();
    playMusic(MOD_RACE);
    setScreenOn();
    fadeIn();

    // countdown
    for (i = 0; i < 90; i++)
    {
        nbig = BIG_FIRST;
        nsmall = SMALL_FIRST;
        raceDrawBike(rival, PLAYER_SX, ry, RF_RIDE);
        raceDrawBike(hero, PLAYER_SX, py, RF_RIDE);
        if (i == 60)
        {
            hudClearRow(12);
            hudTextPal(13, 12, "GO!", 2);
            sfx(SFX_BOOST);
        }
        endFrame();
        hudFlush();
    }
    hudClearRow(12);

    while (1)
    {
        frame++;
        pad0 = padsCurrent(0);
        if (finished)
            pad0 = 0;

        // ---- player
        if (pcrash)
        {
            pcrash--;
            pspeed = 0x40;
        }
        else
        {
            s16 top = (pad0 & KEY_B) ? 0x480 : 0x300;
            if (pboost)
            {
                pboost--;
                top = 0x620;
            }
            if (pspeed < top)
                pspeed += (pad0 & KEY_B) ? 10 : 6;
            else if (pspeed > top)
                pspeed -= 8;
            if (!pspin)
            {
                if ((pad0 & KEY_UP) && py > LANE_TOP)
                    py -= 2;
                if ((pad0 & KEY_DOWN) && py < LANE_BOT)
                    py += 2;
            }
            else
            {
                pspin--;
                py += (frame & 8) ? 1 : -1;
                if (py < LANE_TOP)
                    py = LANE_TOP;
                if (py > LANE_BOT)
                    py = LANE_BOT;
            }
        }
        pfrac += pspeed;
        pdist += pfrac >> 8;
        pfrac &= 0xFF;

        // ---- rival: steady pace with a little rubber band, dodges by lane
        rtimer++;
        if (rcrash)
        {
            rcrash--;
            rspeed = 0x80;
        }
        else
        {
            s16 target = 0x3D0;
            if (rdist + 240 < pdist)
                target = 0x470;
            else if (rdist > pdist + 320)
                target = 0x340;
            if (rspeed < target)
                rspeed += 6;
            else
                rspeed -= 6;
        }
        rfrac += rspeed;
        rdist += rfrac >> 8;
        rfrac &= 0xFF;
        if (ry < laneY(rlane))
            ry += 1;
        if (ry > laneY(rlane))
            ry -= 1;

        // ---- obstacles
        for (i = 0; i < NOBS; i++)
        {
            t = course[i * 3 + 2];
            if (t == O_CAR && ob_x[i] < RACE_LEN + 400)
                ob_x[i] += 2;                           // slow traffic still moves
            oy = laneY(course[i * 3 + 1]);
            // the rival looks ahead and switches lanes around trouble
            if (t != O_BOOST && ob_x[i] > rdist + 40 && ob_x[i] < rdist + 140 && course[i * 3 + 1] == rlane)
                rlane = (rlane == 2) ? 1 : rlane + 1;
            if (ob_hit[i])
                continue;
            if (ob_x[i] + (t == O_CAR ? 56 : (t == O_CONE ? 12 : 28)) > pdist + 8 &&
                ob_x[i] < pdist + 56 && py > oy - 12 && py < oy + 12 && !pcrash)
            {
                ob_hit[i] = 1;
                if (t == O_BOOST)
                {
                    pboost = 70;
                    sfx(SFX_BOOST);
                }
                else if (t == O_OIL)
                {
                    pspin = 40;
                    pspeed >>= 1;
                    sfx(SFX_SPLAT);
                }
                else
                {
                    pcrash = 50;
                    sfx(SFX_CRASH);
                }
            }
        }

        if (!finished && (pdist >= RACE_LEN || rdist >= RACE_LEN))
        {
            finished = 1;
            won = pdist >= RACE_LEN && pdist >= rdist;
            hudClearRow(10);
            if (won)
            {
                hudTextPal(9, 10, "YOU WIN!", 2);
                hudText(6, 12, hero == HERO_JON ? "JON EARNS +1 HEART" : "WES EARNS +1 HEART");
                playMusic(MOD_CLEAR);
            }
            else
            {
                hudTextPal(6, 10, hero == HERO_JON ? "WES GOT THERE FIRST" : "JON GOT THERE FIRST", 2);
                hudText(8, 12, "NO PRIZE THIS TIME");
                spcStop();
            }
        }
        if (finished)
        {
            endtimer++;
            if (endtimer > 300 || (endtimer > 60 && (padsDown(0) & KEY_START)))
                break;
        }
        if ((frame & 7) == 0)
            raceHud();

        // ---- draw: everything sorted roughly by lane so nearer bikes overlap farther ones
        nbig = BIG_FIRST;
        nsmall = SMALL_FIRST;
        f = RF_RIDE + ((frame >> 2) & 1) * 2;
        if (pboost)
            f = RF_BOOST;
        if (pcrash)
            f = RF_CRASH;
        sx = PLAYER_SX + (s16)(rdist - pdist);
        if (ry > py)
        {
            raceDrawBike(hero, PLAYER_SX, py + (pspin ? ((frame & 4) ? 1 : -1) : 0), f);
            raceDrawBike(rival, sx, ry, RF_RIDE + ((frame >> 2) & 1) * 2);
        }
        else
        {
            raceDrawBike(rival, sx, ry, RF_RIDE + ((frame >> 2) & 1) * 2);
            raceDrawBike(hero, PLAYER_SX, py + (pspin ? ((frame & 4) ? 1 : -1) : 0), f);
        }
        for (i = 0; i < NOBS; i++)
        {
            sx = PLAYER_SX + (s16)(ob_x[i] - pdist);
            if (sx < -64 || sx > 256)
                continue;
            t = course[i * 3 + 2];
            oy = laneY(course[i * 3 + 1]);
            if (t == O_CONE)
                drawSmall(sx, oy - 16, ob_hit[i] ? 1 : 0, ATTR_SPRITE(PAL_OBJ), &race_small);
            else if (t == O_CAR)
            {
                drawBig(sx, oy - 32, RB_CAR + ((frame >> 2) & 1) * 2, ATTR_SPRITE(PAL_OBJ), &race_big);
                drawBig(sx + 32, oy - 32, RB_CAR + ((frame >> 2) & 1) * 2 + 1, ATTR_SPRITE(PAL_OBJ), &race_big);
            }
            else
                drawBig(sx, oy - 32 + 4, t == O_OIL ? RB_OIL : RB_BOOST, ATTR_SPRITE(PAL_OBJ), &race_big);
        }
        sx = PLAYER_SX + (s16)(RACE_LEN - pdist) + 48;
        if (sx > -32 && sx < 256)
        {
            drawBig(sx, 112, RB_FLAG, ATTR_SPRITE(PAL_OBJ), &race_big);
            drawBig(sx, 184, RB_FLAG, ATTR_SPRITE(PAL_OBJ), &race_big);
        }
        if (pcrash && (frame & 3) == 0)
            drawSmall(PLAYER_SX + 8, py - 12, 5 + ((frame >> 3) & 1), ATTR_SPRITE(PAL_OBJ), &race_small);

        endFrame();
        bgSetScroll(0, pdist, 0);
        scroll2 = pdist >> 2;
        bgSetScroll(1, scroll2, 0);
        hudFlush();
    }
    fadeOut();
    if (won && hpmax[hero] < 5)
        hpmax[hero]++;
    return won;
}
