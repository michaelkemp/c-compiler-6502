# Path to real hardware

This project's first goal is a correct software emulator + toolchain. This
file tracks what it would additionally take to run the same software on
real hardware (a real 6502, real RAM, and something like an Arduino
bridging I/O) — design notes only for now, not something we're building in
this repo yet.

## What already anticipates real hardware

- Targeting the **original NMOS 6502** (rather than an idealized/cleaned-up
  model) means faithfully reproducing its real quirks (e.g. the `JMP
  (indirect)` page-boundary bug — see `docs/6502-reference.md`). Software
  that only works against a "fixed" emulator wouldn't run correctly on a
  real chip.
- The memory map (`docs/architecture.md`) reserves a dedicated
  memory-mapped I/O region rather than assuming anything CPU-internal for
  I/O — real 6502 systems do I/O this way (e.g. via a VIA/PIA chip), so our
  toy console device sits in the same architectural slot a real I/O chip
  would.
- The assembler (Phase 4, done) emits a flat binary image
  (`AssembledImage(origin, data)`) at a fixed load address — the same kind
  of image you'd burn to an EPROM/flash chip for a real ROM.

## Deliberately deferred: bitmap/graphics display

Nand2Tetris's Hack computer has a memory-mapped bitmap framebuffer (512x256
1-bit pixels) as its screen. We considered the same for Phase 2 and chose a
text console instead (see `docs/architecture.md`), because a bitmap display
is a much bigger lift on both sides of this project:
- **Software**: needs a font/character-set ROM to draw any text, plus an
  actual viewer (e.g. a Tkinter/pygame window) to see the bitmap at all.
- **Hardware**: real bitmap video (sync signals, timing, memory arbitration
  with the CPU) needs dedicated video-generation circuitry -- historically
  a whole separate chip (Apple II's video hardware, the C64's VIC-II,
  etc.) -- something "6502 + RAM + an Arduino" can't produce directly, unlike
  a text console (an Arduino relaying bytes to a serial terminal or a cheap
  character LCD is a realistic build).

Worth revisiting once the text-console toolchain works end-to-end -- as a
later stretch goal, not a Phase 2 requirement.

## What would need to change

- **Timing fidelity**: our emulator is instruction-stepped, not
  cycle-accurate at the bus level (see `docs/architecture.md`). Real
  hardware I/O (e.g. a VIA chip, or an Arduino bit-banging a protocol) may
  care about exact cycle timing in ways our emulator doesn't currently
  model. Revisit if/when this becomes a real build.
- **Real I/O chip**: resolved by decision, see `docs/architecture.md`'s
  Console I/O device section and `docs/roadmap.md`'s Phase 2 follow-up —
  the console device is being remodeled after the real WDC W65C51N ACIA
  rather than staying a made-up protocol, specifically so real hardware
  could use an actual W65C51N chip talking directly to a USB-serial cable
  (no Arduino needed at all for this piece — an Arduino would only enter
  the picture as an alternative bridge if we didn't have/want a real
  ACIA chip).
- **Electrical/bus realities**: bus contention, pull-ups, clock generation,
  reset circuitry, level shifting between the 6502 (5V) and an Arduino
  (often 3.3V or 5V depending on model) — none of this is modeled in
  software and all of it matters for an actual breadboard/PCB build.
- **ROM/RAM chip selection and address decoding**: our memory map assumes
  clean, simple region boundaries; real address decoding logic (glue
  logic/PLD) would need to implement whatever boundaries we pick.

## Status

Not started. Revisit once Phases 1-6 are solid and there's a concrete
hardware build to plan against.
