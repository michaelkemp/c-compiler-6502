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
- The assembler (Phase 4) will emit a flat binary image at a fixed load
  address — the same kind of image you'd burn to an EPROM/flash chip for a
  real ROM.

## What would need to change

- **Timing fidelity**: our emulator is instruction-stepped, not
  cycle-accurate at the bus level (see `docs/architecture.md`). Real
  hardware I/O (e.g. a VIA chip, or an Arduino bit-banging a protocol) may
  care about exact cycle timing in ways our emulator doesn't currently
  model. Revisit if/when this becomes a real build.
- **Real I/O chip**: our `$4000`-`$4001` console device is a toy. A real
  build would use an actual peripheral chip (e.g. a 65C22 VIA) with its own
  register semantics, and the Arduino would sit behind that, not behind our
  made-up protocol. The C runtime's I/O routines would need a different
  low-level implementation, but ideally the same higher-level interface.
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
