; Platform I/O routines for Microsoft BASIC (see docs/roadmap.md's
; "run real Microsoft BASIC" follow-up and scripts/build_msbasic.sh).
;
; Adapted from beneater/msbasic's bios.s (github.com/beneater/msbasic,
; commit 5de42c7, pinned in scripts/fetch_msbasic.sh), which targeted a
; 65C02 + a 6551 ACIA at $5000 + a 6522 VIA for flow control. Changes
; here: ACIA moved to $4000 (our own memory map, docs/architecture.md);
; PHX/PLX (65C02-only) replaced with a stack + Y-register dance (Y is
; free here -- neither BUFFER_SIZE nor READ_BUFFER touch it -- so no new
; zero-page byte is needed; ZP_START0..ZP_START1 is exactly a 2-byte gap
; reserved for this platform file, already fully used by READ_PTR/
; WRITE_PTR, so claiming a 3rd byte there would silently collide with
; BASIC's own zero-page variables); VIA-based flow control removed (no
; VIA in our system, and our software ACIA has no real transmission-rate
; limit to protect against); RESET jumps straight to BASIC's COLD_START
; instead of falling into the WOZMON machine-code monitor first.
.setcpu "6502"
.debuginfo

.zeropage
                .org ZP_START0
READ_PTR:       .res 1
WRITE_PTR:      .res 1

.segment "INPUT_BUFFER"
INPUT_BUFFER:   .res $100

.segment "BIOS"

ACIA_DATA       = $4000
ACIA_STATUS     = $4001
ACIA_CMD        = $4002
ACIA_CTRL       = $4003

LOAD:
                rts

SAVE:
                rts


; Input a character from the serial interface.
; On return, carry flag indicates whether a key was pressed
; If a key was pressed, the key value will be in the A register
;
; Modifies: flags, A
; (Preserves X via the stack + Y instead of PHX/PLX, which NMOS doesn't
; have -- Y is free to use as scratch here since neither BUFFER_SIZE nor
; READ_BUFFER touch it, and Ben Eater's original didn't preserve Y either.
; Must stash the character in Y before restoring X from the stack -- if
; the character sat in A across that restore, popping through A the way
; a naive PHX/PLX-replacement would clobber the value we're returning.)
MONRDKEY:
CHRIN:
                jsr     BUFFER_SIZE
                beq     @no_keypressed
                txa
                pha                     ; save caller's X
                jsr     READ_BUFFER     ; A = character; clobbers X
                tay                     ; stash character in Y
                pla
                tax                     ; restore caller's X
                tya                     ; character back into A
                jsr     CHROUT          ; echo
                sec
                rts
@no_keypressed:
                clc
                rts


; Output a character (from the A register) to the serial interface.
;
; Modifies: flags
MONCOUT:
CHROUT:
                sta     ACIA_DATA
                rts

; Initialize the circular input buffer
; Modifies: flags, A
INIT_BUFFER:
                lda READ_PTR
                sta WRITE_PTR
                rts

; Write a character (from the A register) to the circular input buffer
; Modifies: flags, X
WRITE_BUFFER:
                ldx WRITE_PTR
                sta INPUT_BUFFER,x
                inc WRITE_PTR
                rts

; Read a character from the circular input buffer and put it in the A register
; Modifies: flags, A, X
READ_BUFFER:
                ldx READ_PTR
                lda INPUT_BUFFER,x
                inc READ_PTR
                rts

; Return (in A) the number of unread bytes in the circular input buffer
; Modifies: flags, A
BUFFER_SIZE:
                lda WRITE_PTR
                sec
                sbc READ_PTR
                rts


; Interrupt request handler
; (Preserves A/X via the stack, same NMOS-safe idea as CHRIN's X handling,
; but here the popped A *is* meant to be the original A -- RTI doesn't
; return a value the way CHRIN does -- so popping through the stack in
; reverse push order is correct as-is.)
IRQ_HANDLER:
                pha
                txa
                pha
                lda     ACIA_STATUS
                lda     ACIA_DATA
                jsr     WRITE_BUFFER
                pla
                tax
                pla
                rti

RESET:
                cld
                jsr     INIT_BUFFER
                cli
                lda     #$1F            ; 8-N-1, 19200 bps (irrelevant to the emulator)
                sta     ACIA_CTRL
                ldy     #$09            ; DTR=1, receiver IRQ enabled, no parity
                sty     ACIA_CMD
                jmp     COLD_START      ; straight into BASIC -- no monitor

.segment "RESETVEC"
                .word   $0F00           ; NMI vector (unused)
                .word   RESET           ; RESET vector
                .word   IRQ_HANDLER     ; IRQ vector
