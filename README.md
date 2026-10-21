# COMRADES

A best friend adventure through the stages of life, for the Super Nintendo.

![Title screen](art/screens/title.png)

Play as **Jon** or **Wes** and fight your way through six memories, each with its own
enemies and a boss at the end. Like Super Mario Bros. 2, you pick who plays before every
chapter.

## Play it

Download [`rom/comrades.sfc`](rom/comrades.sfc) and open it in any SNES emulator
(Mesen, bsnes, snes9x). It also runs on real hardware with a flash cart.

| Button | Platforming | Road Ride | The Range |
| --- | --- | --- | --- |
| D-pad | Move | Up/Down change lanes | Aim |
| B | Jump (hold for higher) | Throttle | Fire |
| Y | Throw | | Reload |
| Start | Start / skip | | |

On the title screen, **Select** picks the chapter to start from. Left/Right on a chapter
card switches between Jon and Wes.

You can stomp enemies or hit them with your throw. Hold B while stomping for a big bounce.
Hearts heal you. Hazards (troughs, pits, storm drains, the river, the pool) cost a heart.
If you go down during a boss fight, you restart at the arena door.

**Jon** jumps higher. **Wes** hits harder.

## Chapters

| | Chapter | Boss |
| --- | --- | --- |
| 1 | **FFA Convention**: where Jon and Wes met, flinging grapes off spoons | Champion Bull |
| 2 | **Jam Sessions**: learning guitar at Wes's house | Feedback, the amp stack |
| ★ | **Road Ride**: race the B-King against the RC51 to the diner. A win gives that rider +1 max heart | |
| 3 | **Bar Town Nights**: punk shows, cheap drinks and a long walk home | The Bouncer |
| 4 | **Chicago Fest**: a festival weekend in the windy city | Pigeon King |
| ★ | **The Range**: plates, bottles and clays. Score 25 in 40 seconds and that shooter gets the double shot | |
| 5 | **The Courthouse**: the night shift, mopping a castle of a courthouse | The Judge |
| 6 | **Golden Years**: old friends, still getting into trouble | Father Time |

![Stage 1](art/screens/stage1.png) ![Champion Bull](art/screens/boss1.png)
![Jam Sessions](art/screens/stage2.png) ![Bar Town Nights](art/screens/stage3.png)
![The Bouncer](art/screens/boss3.png) ![Pigeon King](art/screens/boss4.png)
![The Courthouse](art/screens/stage5.png) ![The Judge](art/screens/boss5.png)
![Golden Years](art/screens/stage6.png) ![Chapter card](art/screens/card.png)
![Road Ride](art/screens/race.png) ![The Range](art/screens/range.png)

## Building

Needs [PVSnesLib](https://github.com/alekmaul/pvsneslib) and Python 3 with Pillow and NumPy.

```sh
export PVSNESLIB_HOME=/path/to/pvsneslib
make
```

The ROM is 1MB LoROM. All the art and audio comes from the scripts in `tools/`:

- `heroes.py`: Jon and Wes.
- `stages/`: one script per chapter, built on `stagekit.py`.
- `foes.py`: enemies, bosses and projectiles.
- `bonus.py`: the bikes, the road and the range.
- `font.py` and `title.py`: the logo and the font.
- `music.py`: 12 songs and 15 sound effects, written as Impulse Tracker modules and played by SNESMOD.

`gen_data.py` writes `src/data.asm` and `src/assets.c`. Because the assets are generated,
they stay inside real SNES limits: 16 colour palettes, 8x8 tiles, and 32x32 and 16x16
sprites. Previews of the generated art are in `art/`.

Game code is in `src/`:

- `main.c`: title, chapter cards, flow and ending.
- `stage.c`: the platformer.
- `boss.c`: the bosses.
- `race.c` and `range.c`: the bonus rounds.
