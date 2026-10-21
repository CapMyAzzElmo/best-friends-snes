/*---------------------------------------------------------------------------------

    COMRADES - bonus round: The Range

    A shooting gallery: steel plates pop up on their stands, bottles line the
    fence and clay pigeons sail across the sky. D-pad aims, B fires, Y
    reloads. Score 25 in 40 seconds and the shooter earns the double shot.

---------------------------------------------------------------------------------*/
#include "game.h"

extern char range_big, range_small, bonus_obj_pal;
extern char range_bg1_pic, range_bg1_pic_end, range_bg1_map, range_bg2_pic, range_bg2_pic_end, range_bg2_map,
    range_bg_pal;
extern char font_pic, font_pic_end, ui_pal;

#define GOAL 25
#define TIME_FRAMES 2400
#define NPLATES 3
#define NBOTTLES 5
#define NCLAYS 2
#define AMMO 6

const u8 plate_x[NPLATES] = {36, 116, 196};
const u8 bottle_x[NBOTTLES] = {24, 74, 128, 170, 222};

u8 pl_state[NPLATES], pl_timer[NPLATES];      // state 0 hidden, 1 up, 2 swinging, 3 knocked down
u8 bt_state[NBOTTLES], bt_timer[NBOTTLES];    // state 0 hidden, 1 standing, 2 shattering
u16 cl_x[NCLAYS];
s16 cl_y[NCLAYS], cl_vx[NCLAYS], cl_vy[NCLAYS];
u8 cl_state[NCLAYS], cl_timer[NCLAYS];
s16 cx, cy;
u8 ammo, reload, cooldown, flash, score;
u16 timeleft;

void rangeHud(void)
{
    u8 k;
    hudText(1, 1, "SCORE");
    hudNumber(7, 1, score, 2);
    hudText(11, 1, "/25");
    hudText(17, 1, "TIME");
    hudNumber(22, 1, timeleft / 60, 2);
    for (k = 0; k < AMMO; k++)
        hud[26 * 32 + 2 + k] = (k < ammo ? ('#' - 0x20) : 0) | 0x2000 | (2 << 10);
    hudClearRow(25);
    if (reload)
        hudText(2, 25, "RELOADING");
    else if (ammo == 0)
        hudText(2, 25, "PRESS Y TO RELOAD");
    huddirty = 1;
}

void rangeHit(u8 pts, s16 x, s16 y)
{
    score += pts;
    sfx(pts > 1 ? SFX_POWERUP : SFX_DING);
}

void rangeShoot(void)
{
    u8 k;
    s16 px, py;
    for (k = 0; k < NPLATES; k++)
    {
        px = plate_x[k];
        if (pl_state[k] == 1 && cx > px - 11 && cx < px + 11 && cy > 112 && cy < 136)
        {
            pl_state[k] = 2;
            pl_timer[k] = 10;
            rangeHit(1, px, 124);
            return;
        }
    }
    for (k = 0; k < NBOTTLES; k++)
    {
        px = bottle_x[k];
        if (bt_state[k] == 1 && cx > px + 3 && cx < px + 13 && cy > 104 && cy < 121)
        {
            bt_state[k] = 2;
            bt_timer[k] = 14;
            rangeHit(1, px, 110);
            return;
        }
    }
    for (k = 0; k < NCLAYS; k++)
    {
        px = cl_x[k] >> 4;
        py = cl_y[k] >> 4;
        if (cl_state[k] == 1 && cx > px + 1 && cx < px + 15 && cy > py + 3 && cy < py + 13)
        {
            cl_state[k] = 2;
            cl_timer[k] = 14;
            rangeHit(3, px, py);
            return;
        }
    }
}

u8 rangeRun(void)
{
    u8 k, done = 0, won = 0, lastsec = 0xFF;
    u16 endtimer = 0;

    setScreenOff();
    setBrightness(0);
    oamClear(0, 0);
    setPalette(&range_bg_pal, 0, 256);
    setPalette(&ui_pal, 0, 24);
    setPalette(&range_bg_pal, 0, 2);
    setPalette(&bonus_obj_pal, 128 + 7 * 16, 32);
    dmaCopyVram(&range_bg1_pic, 0x2000, &range_bg1_pic_end - &range_bg1_pic);
    dmaCopyVram(&range_bg2_pic, 0x4000, &range_bg2_pic_end - &range_bg2_pic);
    dmaCopyVram(&range_bg1_map, 0x6800, 64 * 32 * 2);
    dmaCopyVram(&range_bg2_map, 0x7000, 64 * 32 * 2);
    dmaCopyVram(&font_pic, 0x6000, (&font_pic_end - &font_pic));
    screenSetup();
    bgSetScroll(0, 0, 0);
    bgSetScroll(1, 0, 0);
    oamInitDynamicSprite(0x0000, 0x1000, 0, 0, OBJ_SIZE16_L32);
    spritesReset();

    for (k = 0; k < NPLATES; k++)
    {
        pl_state[k] = 0;
        pl_timer[k] = 30 + k * 25;
    }
    for (k = 0; k < NBOTTLES; k++)
    {
        bt_state[k] = 0;
        bt_timer[k] = 20 + k * 30;
    }
    for (k = 0; k < NCLAYS; k++)
    {
        cl_state[k] = 0;
        cl_timer[k] = 120 + k * 90;
    }
    cx = 128;
    cy = 120;
    ammo = AMMO;
    reload = cooldown = flash = score = 0;
    timeleft = TIME_FRAMES;

    hudClear();
    hudTextPal(9, 4, "THE RANGE", 2);
    hudText(3, 6, hero == HERO_JON ? "JON STEPS UP TO THE LINE" : "WES STEPS UP TO THE LINE");
    hudText(2, 8, "HIT 25 TO EARN THE DOUBLE SHOT");
    rangeHud();
    hudFlush();
    playMusic(MOD_RANGE);
    setScreenOn();
    fadeIn();
    for (k = 0; k < 120; k++)
    {
        nbig = BIG_FIRST;
        nsmall = SMALL_FIRST;
        drawSmall(cx - 8, cy - 8, 0, ATTR_SPRITE(PAL_OBJ) | OBJ_PRIO(3), &range_small);
        endFrame();
        hudFlush();
    }
    hudClearRow(4);
    hudClearRow(6);
    hudClearRow(8);

    while (1)
    {
        frame++;
        pad0 = padsCurrent(0);
        padpressed = padsDown(0);
        if (done)
            pad0 = padpressed = 0;

        // aim
        if (pad0 & KEY_LEFT)
            cx -= 3;
        if (pad0 & KEY_RIGHT)
            cx += 3;
        if (pad0 & KEY_UP)
            cy -= 3;
        if (pad0 & KEY_DOWN)
            cy += 3;
        if (cx < 8)
            cx = 8;
        if (cx > 248)
            cx = 248;
        if (cy < 24)
            cy = 24;
        if (cy > 196)
            cy = 196;

        // fire / reload
        if (cooldown)
            cooldown--;
        if (flash)
            flash--;
        if (reload)
        {
            reload--;
            if (reload == 0)
            {
                ammo = AMMO;
                sfx(SFX_SELECT);
                rangeHud();
            }
        }
        else if ((padpressed & KEY_Y) && ammo < AMMO)
        {
            reload = 40;
            rangeHud();
        }
        else if ((padpressed & KEY_B) && !cooldown)
        {
            if (ammo)
            {
                ammo--;
                cooldown = 8;
                flash = 4;
                sfx(SFX_BANG);
                rangeShoot();
                if (ammo == 0)
                    reload = 0;
            }
            rangeHud();
        }

        // targets
        for (k = 0; k < NPLATES; k++)
        {
            if (pl_timer[k])
                pl_timer[k]--;
            if (pl_timer[k] == 0)
            {
                if (pl_state[k] == 0)
                {
                    pl_state[k] = 1;                    // pop up
                    pl_timer[k] = 70 + (rnd() & 63);
                }
                else if (pl_state[k] == 2)
                {
                    pl_state[k] = 3;
                    pl_timer[k] = 30;
                }
                else
                {
                    pl_state[k] = 0;                    // drop back down
                    pl_timer[k] = 30 + (rnd() & 63);
                }
            }
        }
        for (k = 0; k < NBOTTLES; k++)
        {
            if (bt_timer[k])
                bt_timer[k]--;
            if (bt_timer[k] == 0)
            {
                if (bt_state[k] == 0)
                {
                    bt_state[k] = 1;
                    bt_timer[k] = 150;
                }
                else
                {
                    bt_state[k] = 0;
                    bt_timer[k] = 40 + (rnd() & 127);
                }
            }
        }
        for (k = 0; k < NCLAYS; k++)
        {
            if (cl_state[k] == 1)
            {
                cl_x[k] += cl_vx[k];
                cl_y[k] += cl_vy[k];
                cl_vy[k] += 1;
                if ((cl_x[k] >> 4) > 270 || cl_y[k] > (210 << 4))
                {
                    cl_state[k] = 0;
                    cl_timer[k] = 60 + (rnd() & 63);
                }
            }
            else if (cl_state[k] == 2)
            {
                cl_timer[k]--;
                if (cl_timer[k] == 0)
                {
                    cl_state[k] = 0;
                    cl_timer[k] = 60 + (rnd() & 63);
                }
            }
            else
            {
                cl_timer[k]--;
                if (cl_timer[k] == 0 && !done)
                {
                    // launch from the left or the right edge
                    cl_state[k] = 1;
                    cl_y[k] = 150 << 4;
                    cl_vy[k] = -60 - (rnd() & 15);
                    if (rnd() & 1)
                    {
                        cl_x[k] = 0;
                        cl_vx[k] = 30 + (rnd() & 15);
                    }
                    else
                    {
                        cl_x[k] = 250 << 4;
                        cl_vx[k] = -30 - (rnd() & 15);
                    }
                    sfx(SFX_THROW);
                }
            }
        }

        if (!done)
        {
            timeleft--;
            if (timeleft / 60 != lastsec)
            {
                lastsec = timeleft / 60;
                rangeHud();
            }
            if (timeleft == 0)
            {
                done = 1;
                won = score >= GOAL;
                hudClearRow(25);
                hudClearRow(26);
                if (won)
                {
                    hudTextPal(9, 10, "SHARPSHOOTER!", 2);
                    hudText(4, 12, hero == HERO_JON ? "JON EARNS THE DOUBLE SHOT" : "WES EARNS THE DOUBLE SHOT");
                    playMusic(MOD_CLEAR);
                }
                else
                {
                    hudTextPal(10, 10, "TIME'S UP", 2);
                    hudText(5, 12, "NEED 25 FOR THE PRIZE");
                    spcStop();
                }
            }
        }
        else
        {
            endtimer++;
            if (endtimer > 300 || (endtimer > 60 && (padsDown(0) & KEY_START)))
                break;
        }

        // draw
        nbig = BIG_FIRST;
        nsmall = SMALL_FIRST;
        drawSmall(cx - 8, cy - 8, (frame >> 3) & 1, ATTR_SPRITE(PAL_OBJ) | OBJ_PRIO(3), &range_small);
        if (flash)
            drawSmall(cx - 8, cy - 8, 10, ATTR_SPRITE(PAL_OBJ) | OBJ_PRIO(3), &range_small);
        for (k = 0; k < NPLATES; k++)
        {
            if (pl_state[k] == 0)
                continue;
            drawBig(plate_x[k] - 16, 110, pl_state[k] - 1, ATTR_SPRITE(PAL_OBJ), &range_big);
        }
        for (k = 0; k < NBOTTLES; k++)
            if (bt_state[k])
                drawSmall(bottle_x[k], 104, bt_state[k] == 1 ? 2 : 3, ATTR_SPRITE(PAL_OBJ), &range_small);
        for (k = 0; k < NCLAYS; k++)
            if (cl_state[k])
                drawSmall(cl_x[k] >> 4, cl_y[k] >> 4, cl_state[k] == 1 ? 4 + ((frame >> 2) & 1) : 6,
                          ATTR_SPRITE(PAL_OBJ), &range_small);
        endFrame();
        hudFlush();
    }
    fadeOut();
    if (won)
        dblshot[hero] = 1;
    return won;
}
