; Hand-written sprite helpers. drawSmall and drawBig run dozens of times a
; frame, and the C versions spent most of their time recomputing
; &oambuffer[n] for every field.
;
; void drawSmall(s16 x, s16 y, u8 f, u8 attr, char *gfx)
; void drawBig(s16 x, s16 y, u8 f, u8 attr, char *gfx)
; Stack on entry (A16, X16, DB=$7E): 1-3 return, 4 x, 6 y, 8 f, 9 attr, 10 gfx, 12 gfx bank.

.include "hdr.asm"

.section ".fastdraw_text" superfree

drawSmall:
    rep #$30
    lda.w nsmall
    and.w #$00ff
    cmp.w #48                 ; SMALL_LAST + 1
    bcs _dsOut
    asl a
    asl a
    asl a
    asl a
    tax
    lda 4,s
    clc
    adc.w #16
    cmp.w #272                ; -16 <= x <= 255
    bcs _dsOut
    lda 6,s
    clc
    adc.w #16
    cmp.w #241                ; -16 <= y <= 224
    bcs _dsOut
    jsr _fdSet
    sep #$20
    lda.w oambuffer+6,x
    ora.b #1                  ; OBJ_SIZES: the small size
    sta.w oambuffer+6,x
    rep #$20
    lda.w nsmall
    and.w #$00ff
    pha
    jsl oamDynamic16Draw
    pla
    sep #$20
    inc.w nsmall
    rep #$20
_dsOut:
    rtl

drawBig:
    rep #$30
    lda.w nbig
    and.w #$00ff
    cmp.w #16                 ; BIG_LAST + 1
    bcs _dbOut
    asl a
    asl a
    asl a
    asl a
    tax
    lda 4,s
    clc
    adc.w #32
    cmp.w #288                ; -32 <= x <= 255
    bcs _dbOut
    lda 6,s
    clc
    adc.w #32
    cmp.w #257                ; -32 <= y <= 224
    bcs _dbOut
    jsr _fdSet
    lda.w nbig
    and.w #$00ff
    pha
    jsl oamDynamic32Draw
    pla
    sep #$20
    inc.w nbig
    rep #$20
_dbOut:
    rtl

; fills oambuffer entry X from the caller's arguments (2 bytes deeper on the stack
; because of the jsr), flagging a graphics refresh only when the frame changes
_fdSet:
    lda 6,s
    sta.w oambuffer+0,x
    lda 8,s
    sta.w oambuffer+2,x
    sep #$20
    lda 11,s
    sta.w oambuffer+6,x
    rep #$20
    lda 10,s
    and.w #$00ff
    cmp.w oambuffer+4,x
    bne _fdNew
    lda 12,s
    cmp.w oambuffer+8,x
    bne _fdNew
    lda 14,s
    cmp.w oambuffer+10,x
    bne _fdNew
    rts
_fdNew:
    lda 10,s
    and.w #$00ff
    sta.w oambuffer+4,x
    lda 12,s
    sta.w oambuffer+8,x
    lda 14,s
    sta.w oambuffer+10,x
    sep #$20
    lda.b #1
    sta.w oambuffer+7,x
    rep #$20
    rts

.ends

; void shotsMove(void)
; Moves and ages the hero's shots (the Shot structs in stage.c, 12 bytes each:
; x 0, y 2, vx 4, vy 6, alive 8, life 9, kind 10, event 11, power 12), retires the ones
; that land or leave the screen, and boxes the rest for shotHits. A shot that
; needs a spark or a sound gets an event for stage.c: 1 splat, 2 blast.
.define SHOT_SIZE 14
.define SHOT_END 112            ; MAX_SHOTS * SHOT_SIZE

.section ".fastshots_text" superfree

shotsMove:
    php
    rep #$30
    lda.w herox
    clc
    adc.w #16
    sta.w shhx
    lda.w heroy
    clc
    adc.w #14
    sta.w shhy
    lda.w #$7fff
    sta.w shbx0
    sta.w shby0
    lda.w #$8001
    sta.w shbx1
    sta.w shby1
    sep #$20
    stz.w shevents
    rep #$20
    ldx.w #0
_smLoop:
    sep #$20
    stz.w shots+11,x            ; no event
    lda.w shots+8,x             ; alive?
    bne +
    jmp _smNext
+   lda.w shots+9,x             ; life--
    dec a
    sta.w shots+9,x
    sta.w shlifel
    lda.w shots+10,x
    sta.w shkindl
    cmp.b #4                      ; SK_BOOM: just burns down
    bne _smMoving
    lda.w shlifel
    bne +
    jmp _smKill
+   rep #$20
    jsr _smPos
    jmp _smBox

_smMoving:
    rep #$20
    lda.w shots+4,x
    sta.w shvxl
    lda.w shots+6,x
    sta.w shvyl
    sep #$20
    lda.w shkindl
    cmp.b #2                      ; SK_RANG
    beq _smRang
    jmp _smGrav
_smRang:
    lda.w shlifel
    cmp.b #99
    bcc +
    jmp _smStep
+   rep #$20
    jsr _smPos
    ; steer towards the hero: x
    lda.w shpx
    sec
    sbc.w shhx
    bvc +
    eor.w #$8000
+   bpl _smRx1                  ; px >= hx
    lda.w shvxl                 ; px < hx and vx < 80: vx += 5
    sec
    sbc.w #112
    bvc +
    eor.w #$8000
+   bpl _smRy
    lda.w shvxl
    clc
    adc.w #3
    sta.w shvxl
    bra _smRy
_smRx1:
    lda.w shpx
    cmp.w shhx
    beq _smRy
    lda.w shvxl                 ; px > hx and vx > -80: vx -= 5
    sec
    sbc.w #-112
    beq _smRy
    bvc +
    eor.w #$8000
+   bmi _smRy
    lda.w shvxl
    sec
    sbc.w #3
    sta.w shvxl
_smRy:
    lda.w shpy
    sec
    sbc.w shhy
    bvc +
    eor.w #$8000
+   bpl _smRy1
    lda.w shvyl                 ; py < hy and vy < 40: vy += 3
    sec
    sbc.w #24
    bvc +
    eor.w #$8000
+   bpl _smCatch
    lda.w shvyl
    clc
    adc.w #2
    sta.w shvyl
    bra _smCatch
_smRy1:
    lda.w shpy
    cmp.w shhy
    beq _smCatch
    lda.w shvyl                 ; py > hy and vy > -40: vy -= 3
    sec
    sbc.w #-24
    beq _smCatch
    bvc +
    eor.w #$8000
+   bmi _smCatch
    lda.w shvyl
    sec
    sbc.w #2
    sta.w shvyl
_smCatch:
    ; back in the hand: |px - hx| < 12 and |py - hy| < 16, once it has been out a while
    sep #$20
    lda.w shlifel
    cmp.b #80
    rep #$20
    bcs _smStep
    lda.w shpx
    sec
    sbc.w shhx
    clc
    adc.w #11
    cmp.w #23
    bcs _smStep
    lda.w shpy
    sec
    sbc.w shhy
    clc
    adc.w #15
    cmp.w #31
    bcs _smStep
    sep #$20
    stz.w shlifel
    stz.w shots+9,x
    rep #$20
    bra _smStep

_smGrav:
    cmp.b #3                      ; SK_BOMB falls a little faster
    bne +
    rep #$20
    lda.w shvyl
    clc
    adc.w #3
    sta.w shvyl
    bra _smStep
+   cmp.b #1                      ; SK_BOLT flies straight
    beq _smStep
    rep #$20
    lda.w shvyl
    clc
    adc.w #2
    sta.w shvyl

_smStep:
    rep #$20
    lda.w shvxl
    sta.w shots+4,x
    clc
    adc.w shots+0,x
    sta.w shots+0,x
    lda.w shvyl
    sta.w shots+6,x
    clc
    adc.w shots+2,x
    sta.w shots+2,x
    jsr _smPos
    ; a bomb touching the floor goes off
    sep #$20
    lda.w shkindl
    cmp.b #3
    rep #$20
    bne _smEdges
    lda.w shpy
    sec
    sbc.w #187                    ; py > 186
    bvc +
    eor.w #$8000
+   bmi _smEdges
    sep #$20
    lda.b #4
    sta.w shots+10,x            ; SK_BOOM
    lda.b #20
    sta.w shots+9,x
    lda.w shots+12,x            ; a charged bomb burns longer
    beq +
    lda.b #30
    sta.w shots+9,x
+   lda.b #2
    sta.w shots+11,x            ; event: blast
    inc.w shevents
    rep #$20
    stz.w shots+4,x
    stz.w shots+6,x
    lda.w #182*16
    sta.w shots+2,x
    lda.w #182
    sta.w shpy
    bra _smBox

_smEdges:
    ; py > 188 lands
    lda.w shpy
    sec
    sbc.w #189
    bvc +
    eor.w #$8000
+   bmi +
    sep #$20
    lda.w shkindl
    bne _smKill                 ; only grapes splat
    lda.b #1
    sta.w shots+11,x
    inc.w shevents
    bra _smKill
+   lda.w shpy                  ; py < -40
    sec
    sbc.w #-40
    bvc +
    eor.w #$8000
+   bmi _smKill8
    sep #$20
    lda.w shlifel
    beq _smKill
    rep #$20
    lda.w shpx                  ; px + 16 < x_pos
    clc
    adc.w #16
    sec
    sbc.w x_pos
    bvc +
    eor.w #$8000
+   bmi _smKill8
    lda.w x_pos                 ; px > x_pos + 272
    clc
    adc.w #272
    sec
    sbc.w shpx
    bvc +
    eor.w #$8000
+   bmi _smKill8
    bra _smBox

_smKill8:
    sep #$20
_smKill:
    sep #$20
    stz.w shots+8,x
    dec.w nshots
    bra _smNext

_smBox:
    rep #$20
    lda.w shpx
    sec
    sbc.w shbx0
    bvc +
    eor.w #$8000
+   bpl +
    lda.w shpx
    sta.w shbx0
+   lda.w shpx
    sec
    sbc.w shbx1
    bvc +
    eor.w #$8000
+   bmi +
    lda.w shpx
    sta.w shbx1
+   lda.w shpy
    sec
    sbc.w shby0
    bvc +
    eor.w #$8000
+   bpl +
    lda.w shpy
    sta.w shby0
+   lda.w shpy
    sec
    sbc.w shby1
    bvc +
    eor.w #$8000
+   bmi _smNext
    lda.w shpy
    sta.w shby1

_smNext:
    rep #$20
    txa
    clc
    adc.w #SHOT_SIZE
    tax
    cpx.w #SHOT_END
    bcs +
    jmp _smLoop
+   ; widen the box by the biggest hit radius
    lda.w shbx0
    sec
    sbc.w #34
    sta.w shbx0
    lda.w shbx1
    clc
    adc.w #34
    sta.w shbx1
    lda.w shby0
    sec
    sbc.w #34
    sta.w shby0
    lda.w shby1
    clc
    adc.w #34
    sta.w shby1
    plp
    rtl

; shpx = x >> 4 (unsigned), shpy = y >> 4 (signed) for the shot at X. A16.
_smPos:
    lda.w shots+0,x
    lsr a
    lsr a
    lsr a
    lsr a
    sta.w shpx
    lda.w shots+2,x
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    sta.w shpy
    rts

.ends

; void bshotsMove(void)
; Moves the boss's and the foes' shots (the BShot structs in boss.c, 10 bytes
; each: x 0, y 2, vx 4, vy 6 in 1/16 px, alive 8, grav 9), retires the ones
; that leave the screen or land, and checks them against the hero. For
; boss.c it leaves bhit (x of a shot that hit the hero, 0 for none) and
; bland (x of a shot that hit the floor, 0 for none).
.define BSHOT_SIZE 10
.define BSHOT_END 80            ; MAX_BSHOTS * BSHOT_SIZE

.section ".fastbshots_text" superfree

bshotsMove:
    php
    rep #$30
    ldx.w #0
_buLoop:
    sep #$20
    lda.w bshots+8,x
    bne +
    jmp _buNext
+   rep #$20
    lda.w bshots+0,x
    clc
    adc.w bshots+4,x
    sta.w bshots+0,x
    lda.w bshots+2,x
    clc
    adc.w bshots+6,x
    sta.w bshots+2,x
    sep #$20
    lda.w bshots+9,x
    rep #$20
    beq +
    lda.w bshots+6,x
    clc
    adc.w #2
    sta.w bshots+6,x
+   lda.w bshots+0,x
    lsr a
    lsr a
    lsr a
    lsr a
    sta.w bspx
    lda.w bshots+2,x
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    sta.w bspy
    ; off the left or right of the screen
    lda.w bspx
    clc
    adc.w #16
    sec
    sbc.w x_pos
    bpl +
    jmp _buKill
+   lda.w x_pos
    clc
    adc.w #256
    sec
    sbc.w bspx
    bpl +
    jmp _buKill
    ; below the floor (py > 192): lands
+   lda.w bspy
    sec
    sbc.w #193
    bvc +
    eor.w #$8000
+   bmi +
    lda.w bspx
    sta.w bland
    jmp _buKill
    ; far above the screen (py < -32)
+   lda.w bspy
    sec
    sbc.w #-32
    bvc +
    eor.w #$8000
+   bpl +
    jmp _buKill
    ; the hero: 0 < herox + 19 - px < 22 and 0 < heroy + 28 - py < 41 - herotop
+   sep #$20
    lda.w herohp
    rep #$20
    bne +
    jmp _buNext
+   lda.w herox
    clc
    adc.w #18
    sec
    sbc.w bspx                  ; d - 1
    cmp.w #21
    bcs _buNext
    lda.w herotop
    and.w #$00ff
    eor.w #$ffff
    sec
    adc.w #40                   ; 40 - herotop
    sta.w bslim
    lda.w heroy
    clc
    adc.w #27
    sec
    sbc.w bspy                  ; e - 1
    cmp.w bslim
    bcs _buNext
    lda.w bspx
    clc
    adc.w #8
    sta.w bhit
_buKill:
    sep #$20
    stz.w bshots+8,x
    dec.w nbshots
_buNext:
    rep #$20
    txa
    clc
    adc.w #BSHOT_SIZE
    tax
    cpx.w #BSHOT_END
    bcs +
    jmp _buLoop
+   plp
    rtl

.ends

; void shotFind(u16 x0, u16 y0, u16 x1, u16 y1)
; Finds the first live hero shot whose hit radius reaches the box, for
; shotHits in stage.c: shfound = its byte offset in shots[], or $FFFF.
; Stack on entry (A16, X16): 1-3 return, 4 x0, 6 y0, 8 x1, 10 y1.
.section ".fastfind_text" superfree

shotFind:
    php
    rep #$30
    ldx.w #0
_sfLoop:
    sep #$20
    lda.w shots+8,x
    bne +
    jmp _sfNext
+   lda.w shots+10,x              ; radius: blast 22 (34 charged), pick 7, others 3 (6 charged)
    cmp.b #4
    bne _sfNotBoom
    lda.w shots+12,x
    beq +
    lda.b #34
    bra _sfR
+   lda.b #22
    bra _sfR
_sfNotBoom:
    cmp.b #2
    bne +
    lda.b #7
    bra _sfR
+   lda.w shots+12,x
    beq +
    lda.b #6
    bra _sfR
+   lda.b #3
_sfR:
    rep #$20
    and.w #$00ff
    sta.w sfr
    lda.w shots+0,x
    lsr a
    lsr a
    lsr a
    lsr a
    sta.w sfpx
    clc
    adc.w sfr                     ; px + r > x0
    cmp 5,s
    beq _sfNext
    bcc _sfNext
    lda 9,s                       ; px < x1 + r
    clc
    adc.w sfr
    cmp.w sfpx
    beq _sfNext
    bcc _sfNext
    lda.w shots+2,x
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    sta.w sfpy
    clc
    adc.w sfr                     ; py + r > y0
    cmp 7,s
    beq _sfNext
    bcc _sfNext
    lda 11,s                      ; py < y1 + r
    clc
    adc.w sfr
    cmp.w sfpy
    beq _sfNext
    bcc _sfNext
    stx.w shfound
    plp
    rtl
_sfNext:
    rep #$20
    txa
    clc
    adc.w #SHOT_SIZE
    tax
    cpx.w #SHOT_END
    bcs +
    jmp _sfLoop
+   lda.w #$ffff
    sta.w shfound
    plp
    rtl

.ends

; void shotsDraw(void), void sparksDraw(void)
; The hero's shots and the sparks, drawn straight from their arrays. They
; call drawSmall/drawBig like the C code does, through _ds* below: x in dsx,
; y in dsy, frame in dsf, attributes in dsa.
.section ".fastshotdraw_text" superfree

; attributes: OBJ_PRIO(2) | palette << 1
.define A_FOE $24               ; palette 2 (foes A/C, shots, sparks)
.define A_ITEMS $26             ; palette 3 (items)
.define A_SPARK $34             ; palette 2, in front

_dsSmall:                       ; from the stage's small sheet (a_small)
    rep #$20
    lda.w a_small+2
    pha
    lda.w a_small
    pha
    bra _dsPush
_dsItems:                       ; from the items sheet
    rep #$20
    pea.w :items_pic
    pea.w items_pic
_dsPush:
    sep #$20
    lda.w dsa
    pha
    lda.w dsf
    pha
    rep #$20
    lda.w dsy
    pha
    lda.w dsx
    pha
    jsl drawSmall
    rep #$20
    tsc
    clc
    adc.w #10
    tcs
    rts

_dsBoom:                        ; the 32x32 blast
    rep #$20
    pea.w :boom_pic
    pea.w boom_pic
    sep #$20
    lda.w dsa
    pha
    lda.w dsf
    pha
    rep #$20
    lda.w dsy
    pha
    lda.w dsx
    pha
    jsl drawBig
    rep #$20
    tsc
    clc
    adc.w #10
    tcs
    rts

shotsDraw:
    php
    rep #$30
    stz.w dsidx
_sdLoop:
    ldx.w dsidx
    sep #$20
    lda.w shots+8,x
    bne +
    jmp _sdNext
+   lda.w shots+9,x
    sta.w dslife
    lda.w shots+10,x
    sta.w dskind
    lda.w shots+12,x
    sta.w dspow
    rep #$20
    lda.w shots+0,x             ; the shot's centre on screen
    lsr a
    lsr a
    lsr a
    lsr a
    sec
    sbc.w x_pos
    sta.w dscx
    sec
    sbc.w #8
    sta.w dsx
    lda.w shots+2,x
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    sec
    sbc.w y_pos
    sta.w dscy
    sec
    sbc.w #8
    sta.w dsy
    lda.w shots+4,x
    sta.w dsvx
    sep #$20
    lda.w dskind
    beq _sdLob
    cmp.b #1
    beq _sdBolt
    cmp.b #2
    beq _sdRang
    cmp.b #3
    beq _sdBomb
    jmp _sdBoom

_sdLob:                         ; grapes, from the stage sheet
    rep #$20
    inc.w dsx
    inc.w dsx
    inc.w dsy
    inc.w dsy
    lda.w frame
    lsr a
    lsr a
    and.w #1
    sep #$20
    sta.w dsf
    lda.b #A_FOE
    sta.w dsa
    jsr _dsSmall
    jmp _sdTrail

_sdBolt:
    rep #$20
    lda.w frame
    lsr a
    and.w #1
    clc
    adc.w #10                   ; IF_BOLT
    sep #$20
    sta.w dsf
    lda.b #A_ITEMS
    bit.w dsvx+1
    bpl +
    ora.b #$40
+   sta.w dsa
    jsr _dsItems
    jmp _sdTrail

_sdRang:
    rep #$20
    lda.w frame
    lsr a
    lsr a
    and.w #3
    sep #$20
    sta.w dstmp
    and.b #1
    clc
    adc.b #12                   ; IF_RANG
    sta.w dsf
    lda.b #A_ITEMS
    sta.w dsa
    lda.w dstmp
    and.b #2
    beq +
    lda.b #A_ITEMS|$C0
    sta.w dsa
+   jsr _dsItems
    jmp _sdTrail

_sdBomb:
    rep #$20
    lda.w frame
    lsr a
    lsr a
    and.w #1
    clc
    adc.w #14                   ; IF_BOMB
    sep #$20
    sta.w dsf
    lda.b #A_ITEMS
    sta.w dsa
    jsr _dsItems
    jmp _sdTrail

_sdBoom:                        ; one 32x32 sprite, plus a ring of quarters when charged
    sep #$20
    lda.w dslife
    cmp.b #15
    bcc +
    lda.b #0
    bra ++
+   cmp.b #8
    lda.b #1
    bcs ++
    lda.b #2
++  sta.w dsf
    lda.b #A_ITEMS
    sta.w dsa
    rep #$20
    lda.w dscx
    sec
    sbc.w #16
    sta.w dsx
    lda.w dscy
    sec
    sbc.w #16
    sta.w dsy
    jsr _dsBoom
    sep #$20
    lda.w dspow
    bne +
    jmp _sdNext
+   lda.w dsf
    clc
    adc.b #16                   ; IF_BOOM
    sta.w dsf
    rep #$20
    lda.w dscx                  ; left
    sec
    sbc.w #30
    sta.w dsx
    lda.w dscy
    sec
    sbc.w #8
    sta.w dsy
    jsr _dsItems
    rep #$20
    lda.w dscx                  ; right
    clc
    adc.w #14
    sta.w dsx
    sep #$20
    lda.b #A_ITEMS|$40
    sta.w dsa
    jsr _dsItems
    rep #$20
    lda.w dscx                  ; top
    sec
    sbc.w #8
    sta.w dsx
    lda.w dscy
    sec
    sbc.w #30
    sta.w dsy
    sep #$20
    lda.b #A_ITEMS
    sta.w dsa
    jsr _dsItems
    rep #$20
    lda.w dscy                  ; bottom
    clc
    adc.w #14
    sta.w dsy
    sep #$20
    lda.b #A_ITEMS|$C0
    sta.w dsa
    jsr _dsItems
    jmp _sdNext

_sdTrail:                       ; charged shots leave sparks behind
    sep #$20
    lda.w dspow
    beq _sdNext
    lda.w frame
    and.b #1
    beq _sdNext
    rep #$20
    lda.w dsvx                  ; x = cx - 8 - (vx >> 3)
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    cmp.w #$8000
    ror a
    eor.w #$ffff
    sec
    adc.w dscx
    sec
    sbc.w #8
    sta.w dsx
    lda.w dscy
    sec
    sbc.w #8
    sta.w dsy
    lda.w frame
    lsr a
    and.w #1
    clc
    adc.w #2                    ; SF_SPARK
    sep #$20
    sta.w dsf
    lda.b #A_SPARK
    sta.w dsa
    jsr _dsSmall

_sdNext:
    rep #$20
    lda.w dsidx
    clc
    adc.w #SHOT_SIZE
    sta.w dsidx
    cmp.w #SHOT_END
    bcs +
    jmp _sdLoop
+   plp
    rtl

sparksDraw:
    php
    rep #$30
    stz.w dsidx
_spLoop:
    ldx.w dsidx
    sep #$20
    lda.w sptime,x
    beq _spNext
    sta.w dstmp
    dec a
    sta.w sptime,x
    bne +
    dec.w nsparks
+   lda.b #12                   ; SF_SPARK + (12 - time) / 4
    sec
    sbc.w dstmp
    lsr a
    lsr a
    clc
    adc.b #2
    sta.w dsf
    lda.b #A_SPARK
    sta.w dsa
    rep #$20
    txa
    asl a
    tax
    lda.w spx,x
    sec
    sbc.w x_pos
    sta.w dsx
    lda.w spy,x
    sec
    sbc.w y_pos
    sta.w dsy
    jsr _dsSmall
_spNext:
    rep #$20
    inc.w dsidx
    lda.w dsidx
    cmp.w #6                    ; MAX_SPARKS
    bcc _spLoop
    plp
    rtl


; void foesDraw(void): the active foes (stage.c's actlist), A and B kinds as
; 32x32 sprites from a_foes, C kinds as 16x16 from a_small
_dsFoeBig:
    rep #$20
    lda.w a_foes+2
    pha
    lda.w a_foes
    pha
    sep #$20
    lda.w dsa
    pha
    lda.w dsf
    pha
    rep #$20
    lda.w dsy
    pha
    lda.w dsx
    pha
    jsl drawBig
    rep #$20
    tsc
    clc
    adc.w #10
    tcs
    rts

foesDraw:
    php
    rep #$30
    stz.w dsidx
_fdLoop:
    sep #$20
    lda.w dsidx
    cmp.w nact
    bcc +
    plp
    rtl
+   rep #$20
    lda.w dsidx
    and.w #$00ff
    tax
    lda.w actlist,x
    and.w #$00ff
    tax                         ; X: foe number
    sep #$20
    lda.w fstate,x
    cmp.b #3                    ; FOE_DEAD
    bne +
    jmp _fdNext
+   sta.w dstmp
    lda.w fkind,x
    sta.w dskind
    lda.w fframe,x
    sta.w dsf
    lda.w fdir,x                ; facing right unless fdir is 0; flipped back while hurt
    beq +
    lda.b #0
    bra ++
+   lda.b #$40
++  sta.w dsa
    rep #$20
    txa
    asl a
    tax                         ; X: word index
    lda.w fx,x
    sec
    sbc.w x_pos
    sta.w dsx
    clc
    adc.w #32
    cmp.w #289                  ; -32 <= sx <= 256
    bcc +
    jmp _fdNext
+   lda.w fy,x
    clc
    adc.w fhop,x
    sec
    sbc.w y_pos
    sta.w dsy
    sep #$20
    lda.w dstmp
    cmp.b #2
    bne +
    lda.w dsa
    eor.b #$40
    sta.w dsa
+   lda.w dskind
    cmp.b #3                    ; KIND_C
    bne _fdBig
    lda.w dsa
    ora.b #$24                  ; palette 2
    sta.w dsa
    rep #$20
    lda.w dsy
    sec
    sbc.w #16
    sta.w dsy
    jsr _dsSmall
    jmp _fdNext
_fdBig:
    cmp.b #2                    ; KIND_B: palette 5, frames from 7
    bne +
    lda.w dsa
    ora.b #$2A
    sta.w dsa
    lda.w dsf
    clc
    adc.b #7
    sta.w dsf
    bra ++
+   lda.w dsa
    ora.b #$24
    sta.w dsa
++  rep #$20
    lda.w dsy
    sec
    sbc.w #32
    sta.w dsy
    jsr _dsFoeBig
_fdNext:
    rep #$20
    inc.w dsidx
    jmp _fdLoop

.ends
