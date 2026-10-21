/*---------------------------------------------------------------------------------

    COMRADES - shared declarations

    VRAM map (word addresses)
      0x0000  large (32x32) dynamic sprite graphics
      0x1000  small (16x16) dynamic sprite graphics
      0x2000  BG1 tiles (stage tiles, title logo from tile 256)
      0x4000  BG2 tiles (backdrop)
      0x6000  BG3 tiles (2bpp font + HUD icons)
      0x6800  BG1 map 64x32 (map engine)
      0x7000  BG2 map 64x32
      0x7800  BG3 map 32x32 (HUD / text)

    Sprite palettes: 0 Jon, 1 Wes, 2 foes A/C + shots, 3/4 dimmed heroes or
    bikes, 5 foe B, 6 boss, 7 bonus round objects

---------------------------------------------------------------------------------*/
#ifndef GAME_H
#define GAME_H

#include <snes.h>
#include "build/soundbank.h"
#include "build/sfx.h"

#define HERO_JON 0
#define HERO_WES 1
#define NSTAGES 6

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

#define ATTR_SPRITE(pal) (OBJ_PRIO(2) | ((pal) << 1))
#define PAL_HERO_DIM 3
#define PAL_ITEMS 3
#define PAL_FOE_A 2
#define PAL_FOE_B 5
#define PAL_BOSS 6
#define PAL_OBJ 7

// dynamic sprite buffer: large sprites draw from entry 0, small from entry 16
#define BIG_FIRST 0
#define BIG_LAST 15
#define SMALL_FIRST 16
#define SMALL_LAST 47

// items sheet frames (see tools/items.py)
#define IF_FLAG_DOWN 0
#define IF_FLAG_UP 1
#define IF_1UP 3
#define IF_STAR 4
#define IF_WEAPON 6        // + weapon - 1
#define IF_BOLT 10
#define IF_RANG 12
#define IF_BOMB 14
#define IF_BOOM 16
#define IF_PROP 19         // + stage * 2 (+1 cracked)
#define IF_SPARKLE 31

// pickups hidden in breakable props (match tools/stagekit.py)
#define ITEM_STAR 0
#define ITEM_HEART 1
#define ITEM_1UP 2
#define ITEM_SPREAD 3
#define ITEM_RAPID 4
#define ITEM_RANG 5
#define ITEM_BOMB 6

// weapons
#define W_LOB 0
#define W_SPREAD 1
#define W_RAPID 2
#define W_RANG 3
#define W_BOMB 4

// ---------------------------------------------------------------- main.c
extern u8 hero, stage;
extern u8 hpmax[2], dblshot[2];
extern u8 lives, weapon;
extern u16 score, next1up;      // score counts tens of points
extern u16 pad0, padpressed;
extern u16 frame;
extern u16 hud[32 * 32];
extern u8 huddirty, hudrows;
extern u16 lastscore;
extern u8 nbig, nsmall;
extern u16 rng;

void waitFrame(void);
void sfx(u8 id);
void playMusic(u8 mod);
void hudClear(void);
void hudText(u16 x, u16 y, char *s);
void hudTextPal(u16 x, u16 y, char *s, u8 pal);
void hudClearRow(u16 y);
void hudNumber(u16 x, u16 y, u16 v, u8 digits);
void hudFlush(void);
void fadeIn(void);
void fadeOut(void);
void screenSetup(void);
void spritesReset(void);
void drawBig(s16 x, s16 y, u8 f, u8 attr, char *gfx);
void drawSmall(s16 x, s16 y, u8 f, u8 attr, char *gfx);
void endFrame(void);
u16 rnd(void);
void addScore(u16 tens);
void hudScore(void);
u8 centre(char *s);
u8 slen(char *s);

// ---------------------------------------------------------------- assets.c
extern char *a_map, *a_bg1pic, *a_tiledef, *a_tileprop, *a_bgpal, *a_hero;
extern char *a_bg2pic, *a_bg2map, *a_foes, *a_small, *a_boss, *a_spra, *a_sprb, *a_bosspal;
extern u16 a_bg1size, a_bg2size;
extern u16 *a_foetab, *a_hearttab, *a_proptab, *a_cptab;
extern u16 a_nfoes, a_nhearts, a_nprops, a_arenax;
void loadStageAssets(u8 s);

// ---------------------------------------------------------------- stage.c
extern u16 herox, heroy;
extern s16 *heroxv, *heroyv;
extern u8 herohp, heroinvuln, heroyofs, stagedone;
extern u16 bossarena;
void heroHurt(s16 fromx);
void heroBounce(s16 vy);
void spawnSpark(u16 x, u16 y);
void stageStart(u8 respawn);
u8 stageLoop(void);
u8 playStageLoop(void);
u8 shotHits(u16 x0, u16 y0, u16 x1, u16 y1);
#define STAGE_CLEAR 1
#define STAGE_GAMEOVER 2
#define STAGE_QUIT 3

// ---------------------------------------------------------------- boss.c
extern u8 bossactive, bossdead;
void bossInit(void);
void bossStart(void);
void bossUpdate(void);
void bossDraw(void);

// ---------------------------------------------------------------- race.c / range.c
u8 raceRun(u8 variant);
u8 rangeRun(u8 variant);

#endif
