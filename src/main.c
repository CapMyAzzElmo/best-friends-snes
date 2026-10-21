/*---------------------------------------------------------------------------------

    COMRADES - a best friend adventure through the stages of life

    main.c: shared helpers (sound, HUD text, fades, dynamic sprites), the
    title screen, the chapter cards with character select, the ending and
    the overall game flow:

      six chapters, each followed by a bonus round (Road Ride and The Range
      take turns), then the ending

---------------------------------------------------------------------------------*/
#include "game.h"

extern char SOUNDBANK__0, SOUNDBANK__1, SOUNDBANK__2, SOUNDBANK__3;
extern char logo_pic, logo_pic_end, logo_pal, title_bg1_map, font_pic, font_pic_end, ui_pal;
extern char jon_pic, jon_pal, jon_dim_pal, wes_pic, wes_pal, wes_dim_pal;
extern char st1_bg1_pic, st1_bg1_pic_end, st1_bg_pal, st1_bg2_pic, st1_bg2_pic_end, st1_bg2_map;

u8 hero, stage;
u8 hpmax[2], dblshot[2];
u8 lives, weapon;
u16 score, next1up;
u16 pad0, padpressed;
u16 frame;
u16 rng = 0x2F6B;
u8 startstage;

// ---------------------------------------------------------------- frame pacing and sound
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
    u8 k;
    spcStop();
    spcLoad(mod);
    for (k = 0; k < SFX_COUNT; k++)
        spcLoadEffect(k);
    spcPlay(0);
}

u16 rnd(void)
{
    // 16-bit xorshift
    rng ^= rng << 7;
    rng ^= rng >> 9;
    rng ^= rng << 8;
    return rng;
}

// ---------------------------------------------------------------- HUD (BG3)
u16 hud[32 * 32];
u8 huddirty;
u8 hudrows = 32;       // rows to upload on the next flush (the HUD bar is rows 0-3)

void hudClear(void)
{
    u16 k;
    for (k = 0; k < 32 * 32; k++)
        hud[k] = 0;
    huddirty = 1;
    hudrows = 32;
}

void hudTextPal(u16 x, u16 y, char *s, u8 pal)
{
    u16 p = y * 32 + x;
    if (y >= hudrows)
        hudrows = y + 1;
    while (*s)
    {
        hud[p] = ((*s) - 0x20) | 0x2000 | (pal << 10);
        p++;
        s++;
    }
    huddirty = 1;
}

void hudText(u16 x, u16 y, char *s)
{
    hudTextPal(x, y, s, 0);
}

void hudClearRow(u16 y)
{
    u16 k;
    for (k = 0; k < 32; k++)
        hud[y * 32 + k] = 0;
    huddirty = 1;
    if (y >= hudrows)
        hudrows = y + 1;
}

void hudNumber(u16 x, u16 y, u16 v, u8 digits)
{
    u16 p = y * 32 + x + digits - 1;
    if (y >= hudrows)
        hudrows = y + 1;
    while (digits)
    {
        hud[p] = (('0' + (v % 10)) - 0x20) | 0x2000;
        v /= 10;
        p--;
        digits--;
    }
    huddirty = 1;
}

void hudFlush(void)
{
    if (huddirty)
    {
        // only the rows that may have changed, to keep the vblank short
        dmaCopyVram((u8 *)hud, 0x7800, hudrows << 6);
        huddirty = 0;
        hudrows = 4;
    }
}

u8 slen(char *s)
{
    u8 n = 0;
    while (s[n])
        n++;
    return n;
}

// score: tens of points, shown with a trailing zero; an extra life every 20000
void hudScore(void)
{
    hud[1 * 32 + 21] = 0x45 | 0x2000 | (2 << 10);
    hudNumber(23, 1, score, 5);
    hudText(28, 1, "0");
    lastscore = score;
}

void addScore(u16 tens)
{
    if (score > 65000 - tens)
        score = 65000;
    else
        score += tens;
    if (score >= next1up)
    {
        next1up += 2000;
        if (lives < 99)
            lives++;
        sfx(SFX_ONEUP);
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

void screenSetup(void)
{
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
// always use oambuffer[BIG_FIRST..] and small ones oambuffer[SMALL_FIRST..]
// in the order they are drawn: entry n then always owns the same VRAM slot
// and only needs a re-upload when what it shows changes.
u8 nbig, nsmall;

void spritesReset(void)
{
    u8 k;
    for (k = 0; k <= SMALL_LAST; k++)
    {
        oambuffer[k].oamgraphics = 0;
        oambuffer[k].oamframeid = 0xFF;
    }
    nbig = BIG_FIRST;
    nsmall = SMALL_FIRST;
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

// drawBig and drawSmall are in fast.asm

void endFrame(void)
{
    oamInitDynamicSpriteEndFrame();
    spcProcess();
    WaitForVBlank();
    hudFlush();    // text first: it is small, and late in the vblank it would be lost
    oamVramQueueUpdate();
}

// ---------------------------------------------------------------- the shared menu backdrop
// Title, chapter cards and the ending sit on the FFA hall: the logo or the
// story text over the arena floor, with the friends standing on it.
void menuScreen(u8 withlogo)
{
    setScreenOff();
    setBrightness(0);
    oamClear(0, 0);
    setPalette(&st1_bg_pal, 0, 256);
    setPalette(&ui_pal, 0, 24);
    setPalette(&st1_bg_pal, 0, 2);
    setPalette(&logo_pal, 48, 32);
    setPalette(&jon_pal, 128, 32);
    setPalette(&wes_pal, 144, 32);
    setPalette(&jon_dim_pal, 176, 32);
    setPalette(&wes_dim_pal, 192, 32);
    dmaCopyVram(&st1_bg1_pic, 0x2000, (&st1_bg1_pic_end - &st1_bg1_pic));
    dmaCopyVram(&logo_pic, 0x3000, (&logo_pic_end - &logo_pic));
    dmaCopyVram(&st1_bg2_pic, 0x4000, (&st1_bg2_pic_end - &st1_bg2_pic));
    dmaCopyVram(&st1_bg2_map, 0x7000, 64 * 32 * 2);
    dmaCopyVram(&font_pic, 0x6000, (&font_pic_end - &font_pic));
    dmaCopyVram(&title_bg1_map, 0x6800, 64 * 32 * 2);
    screenSetup();
    if (!withlogo)
        bgSetDisable(0);
    bgSetScroll(0, 0, 0);
    bgSetScroll(1, 0, 0);
    oamInitDynamicSprite(0x0000, 0x1000, 0, 0, OBJ_SIZE16_L32);
    spritesReset();
    hudClear();
}

// draw both friends; the chosen one runs in place, the other waits dimmed
void drawFriends(u8 chosen, u16 anim, s16 y, u8 cheer)
{
    u8 k, f, mine;
    nbig = BIG_FIRST;
    nsmall = SMALL_FIRST;
    for (k = 0; k < 2; k++)
    {
        mine = (k == chosen) || cheer;
        if (cheer)
            f = ((anim >> 4) & 1) ? F_CHEER : F_IDLE;
        else
            f = mine ? F_RUN + ((anim >> 2) & 7) : F_IDLE + ((anim >> 4) & 3);
        drawBig(k ? 168 : 56, y, f, ATTR_SPRITE(mine ? k : PAL_HERO_DIM + k) | (k ? 0x40 : 0), k ? &wes_pic : &jon_pic);
    }
}

// ---------------------------------------------------------------- title
char *const chapter_name[6] = {"FFA CONVENTION", "JAM SESSIONS", "BAR TOWN NIGHTS", "CHICAGO FEST",
                               "THE COURTHOUSE", "GOLDEN YEARS"};

void titleDrawStart(void)
{
    hudClearRow(23);
    hudText(7, 23, "START AT CHAPTER");
    hudNumber(24, 23, startstage + 1, 1);
    hudClearRow(24);
    hudTextPal(16 - 7, 24, chapter_name[startstage], 2);
}

void titleScreen(void)
{
    u16 anim = 0;
    menuScreen(1);
    hudText(6, 9, "A BEST FRIEND STORY");
    hudText(10, 26, "PRESS START");
    hudText(4, 27, "SELECT: PICK A CHAPTER");
    startstage = 0;
    titleDrawStart();
    hudFlush();
    playMusic(MOD_TITLE);
    setScreenOn();
    fadeIn();
    while (1)
    {
        anim++;
        rnd();
        padpressed = padsDown(0);
        if (padpressed & KEY_SELECT)
        {
            startstage = (startstage + 1) % NSTAGES;
            titleDrawStart();
            sfx(SFX_SELECT);
        }
        if (padpressed & (KEY_START | KEY_A))
        {
            sfx(SFX_JUMP);
            break;
        }
        if ((anim & 31) == 0)
        {
            if (anim & 32)
                hudClearRow(26);
            else
                hudText(10, 26, "PRESS START");
        }
        drawFriends(2, anim, 144, 1);
        endFrame();
        bgSetScroll(1, anim >> 2, 0);
        hudFlush();
    }
    fadeOut();
}

// ---------------------------------------------------------------- chapter cards
// line 1 heading, then two lines of story
char *const card_text[24] = {
    "CHAPTER 1", "FFA CONVENTION", "WHERE JON AND WES FIRST MET,", "FLINGING GRAPES OFF SPOONS.",
    "CHAPTER 2", "JAM SESSIONS", "LEARNING GUITAR TOGETHER", "AT WES'S HOUSE.",
    "CHAPTER 3", "BAR TOWN NIGHTS", "PUNK BANDS, CHEAP DRINKS", "AND A LONG WALK HOME.",
    "CHAPTER 4", "CHICAGO FEST", "A FESTIVAL WEEKEND", "IN THE WINDY CITY.",
    "CHAPTER 5", "THE COURTHOUSE", "THE NIGHT SHIFT, MOPPING", "A CASTLE OF A COURTHOUSE.",
    "CHAPTER 6", "GOLDEN YEARS", "OLD FRIENDS, STILL", "GETTING INTO TROUBLE."};
// one bonus round after each chapter but the last
char *const bonus_text[20] = {
    "BONUS ROUND", "ROAD RIDE", "RACE THE B-KING AND THE RC51", "TO THE DINER. WIN: +1 HEART",
    "BONUS ROUND", "THE RANGE", "HIT 25 TARGETS IN 40 SECONDS", "FOR AN EXTRA LIFE",
    "BONUS ROUND", "MIDNIGHT RUN", "RACE HOME THROUGH THE NIGHT", "WIN: +1 HEART",
    "BONUS ROUND", "DUSK AT THE RANGE", "FASTER TARGETS, LOW LIGHT", "HIT 25 FOR AN EXTRA LIFE",
    "BONUS ROUND", "SUNSET RIDE", "ONE LAST RACE DOWN THE COAST", "WIN: +1 HEART"};

u8 centre(char *s)
{
    return (32 - slen(s)) >> 1;
}

void cardPerks(void)
{
    u8 k;
    hudClearRow(22);
    hudClearRow(23);
    hudClearRow(2);
    hud[2 * 32 + 3] = 0x44 | 0x2000 | (2 << 10);
    hudText(4, 2, "X");
    hudNumber(5, 2, lives, 2);
    hudText(18, 2, "SCORE");
    hudNumber(24, 2, score, 5);
    hudText(29, 2, "0");
    for (k = 0; k < 2; k++)
    {
        u8 x = k ? 19 : 5;
        if (hpmax[k] > 3)
        {
            hudText(x, 22, "+");
            hudNumber(x + 1, 22, hpmax[k] - 3, 1);
            hudText(x + 2, 22, " HEART");
        }
        if (dblshot[k])
            hudText(x, 23, "DOUBLE SHOT");
    }
}

void cardChoice(void)
{
    hudClearRow(20);
    hudTextPal(7, 20, "JON", hero == HERO_JON ? 2 : 0);
    hudTextPal(21, 20, "WES", hero == HERO_WES ? 2 : 0);
    hudText(hero == HERO_JON ? 5 : 19, 20, ">");
    hudClearRow(26);
    hudText(hero == HERO_JON ? 3 : 17, 26, hero == HERO_JON ? "JUMPS HIGHER" : "HITS HARDER");
}

// a chapter card with the story and the SMB2 style pick of who plays, over
// the backdrop of the stage to come (bonus rounds keep the FFA hall)
void chapterCard(char *const *text, u8 isstage)
{
    u16 anim = 0;
    menuScreen(0);
    if (isstage)
    {
        loadStageAssets(stage);
        setPalette(a_bgpal + 5 * 32, 5 * 16, 64);
        setPalette(a_bgpal, 0, 2);
        dmaCopyVram(a_bg2pic, 0x4000, a_bg2size);
        dmaCopyVram(a_bg2map, 0x7000, 64 * 32 * 2);
    }
    hudTextPal(centre(text[0]), 4, text[0], 2);
    hudTextPal(centre(text[1]), 6, text[1], 2);
    hudText(centre(text[2]), 10, text[2]);
    hudText(centre(text[3]), 12, text[3]);
    hudText(7, 16, "WHO'S UP? PRESS START");
    cardChoice();
    cardPerks();
    hudFlush();
    setScreenOn();
    fadeIn();
    while (1)
    {
        anim++;
        rnd();
        padpressed = padsDown(0);
        if (padpressed & (KEY_LEFT | KEY_RIGHT | KEY_SELECT))
        {
            hero ^= 1;
            cardChoice();
            sfx(SFX_SELECT);
        }
        if ((padpressed & (KEY_START | KEY_A | KEY_B)) && anim > 20)
        {
            sfx(SFX_JUMP);
            break;
        }
        drawFriends(hero, anim, 176, 0);
        endFrame();
        hudFlush();
    }
    fadeOut();
}

// ---------------------------------------------------------------- ending
char *const ending_text[10] = {
    "FROM GRAPES ON SPOONS",
    "TO GUITARS AND PUNK SHOWS,",
    "FESTIVALS AND NIGHT SHIFTS,",
    "BIKES, BULLSEYES",
    "AND BINGO NIGHTS...",
    "SOME FRIENDS ARE",
    "FOR A SEASON.",
    "",
    "JON AND WES ARE",
    "COMRADES FOR LIFE."};

void ending(void)
{
    u16 anim = 0, k;
    u8 line = 0;
    menuScreen(1);
    hudFlush();
    playMusic(MOD_ENDING);
    setScreenOn();
    fadeIn();
    while (1)
    {
        anim++;
        if (line < 10 && (anim % 90) == 0)
        {
            // two pages of five lines, double spaced above the friends
            if (line == 5)
                for (k = 8; k < 18; k++)
                    hudClearRow(k);
            hudTextPal(centre(ending_text[line]), 8 + (line % 5) * 2, ending_text[line], line >= 8 ? 2 : 0);
            line++;
            if (line == 10)
            {
                hudText(7, 20, "FINAL SCORE");
                hudNumber(19, 20, score, 5);
                hudText(24, 20, "0");
                hudTextPal(12, 24, "THE END", 2);
                hudText(7, 26, "THANKS FOR PLAYING");
            }
        }
        if (line == 10 && anim > 1000 && (padsDown(0) & KEY_START))
            break;
        drawFriends(2, anim, 144, 1);
        endFrame();
        bgSetScroll(1, anim >> 2, 0);
        hudFlush();
    }
    fadeOut();
}

// ---------------------------------------------------------------- game flow
// out of lives: continue from the start of the chapter, or give up
u8 gameOver(void)
{
    u8 sel = 0, anim = 0;
    menuScreen(0);
    hudTextPal(11, 8, "GAME OVER", 2);
    hudText(9, 12, "FINAL SCORE");
    hudNumber(10, 14, score, 5);
    hudText(15, 14, "0");
    spcStop();
    setScreenOn();
    fadeIn();
    while (1)
    {
        anim++;
        hudClearRow(18);
        hudTextPal(8, 18, "CONTINUE", sel == 0 ? 2 : 0);
        hudTextPal(19, 18, "QUIT", sel == 1 ? 2 : 0);
        hudText(sel ? 17 : 6, 18, ">");
        padpressed = padsDown(0);
        if (padpressed & (KEY_LEFT | KEY_RIGHT | KEY_SELECT))
        {
            sel ^= 1;
            sfx(SFX_SELECT);
        }
        if ((padpressed & (KEY_START | KEY_A | KEY_B)) && anim > 30)
            break;
        drawFriends(hero, 0, 176, 0);
        endFrame();
        hudFlush();
    }
    fadeOut();
    return sel == 0;
}

// returns 0 when the player quits to the title
u8 playStage(void)
{
    u8 r;
    chapterCard(&card_text[stage * 4], 1);
    while (1)
    {
        stageStart(1);
        r = stageLoop();
        fadeOut();
        if (r == STAGE_CLEAR)
            return 1;
        if (r == STAGE_QUIT)
            return 0;
        // game over
        if (!gameOver())
            return 0;
        lives = 3;
        score = 0;
        next1up = 2000;
        chapterCard(&card_text[stage * 4], 1);
    }
}

void playBonus(void)
{
    u8 b = stage;    // 0 race, 1 range, 2 race at night, 3 range at dusk, 4 race at sunset
    chapterCard(&bonus_text[b * 4], 0);
    if (b & 1)
        rangeRun(b >> 1);
    else
        raceRun(b >> 1);
}

int main(void)
{
    spcBoot();
    // the soundbank spans three banks; naming each keeps the linker from dropping them
    spcSetBank(&SOUNDBANK__3);
    spcSetBank(&SOUNDBANK__2);
    spcSetBank(&SOUNDBANK__1);
    spcSetBank(&SOUNDBANK__0);
    consoleInit();
    while (1)
    {
        titleScreen();
        hpmax[0] = hpmax[1] = 3;
        dblshot[0] = dblshot[1] = 0;
        lives = 3;
        weapon = W_LOB;
        score = 0;
        next1up = 2000;
        hero = HERO_JON;
        for (stage = startstage; stage < NSTAGES; stage++)
        {
            if (!playStage())
                break;
            if (stage < NSTAGES - 1)
                playBonus();
        }
        if (stage == NSTAGES)
            ending();
    }
    return 0;
}
