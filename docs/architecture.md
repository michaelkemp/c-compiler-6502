# System architecture

## Memory map (draft — custom, not copied from an existing board)

A simple map, small enough to reason about, with room to grow:

```
$0000-$00FF  Zero page (fast addressing modes; also used by our future
             compiler for pointers/temporaries)
$0100-$01FF  Hardware stack (used by JSR/RTS/PHA/PLA/interrupts — not
             available to the C compiler as a call stack, see below)
$0200-$3FFF  RAM (general purpose; software parameter/data stack for the
             compiler lives at the top of this region, growing downward)
$4000-$40FF  Memory-mapped I/O (console device: see below)
$4100-$7FFF  Reserved / unused for now
$8000-$FFF9  ROM (program code)
$FFFA-$FFFB  NMI vector
$FFFC-$FFFD  RESET vector
$FFFE-$FFFF  IRQ/BRK vector
```

This is a starting point for Phase 2 — adjust freely once we're actually
writing programs against it and find the boundaries inconvenient. Update
this file whenever the map changes; it's the single source of truth for
both the emulator's `Bus` implementation and anything we write in
assembly/C.

## Console I/O device (implemented, Phase 2)

A minimal memory-mapped device at `$4000`-`$4001`
(`src/c6502/emulator/devices.py`'s `ConsoleDevice`):

- `$4000` — **output register**: writing a byte here appends it (e.g. as an
  ASCII character) to the emulator's console output (`console.output_text`).
- `$4001` — **input register**: reading it pops and returns the next
  queued input byte, or `0` if none is waiting. A program feeds input via
  `console.feed_input(...)` — there's no live stdin/stdout hookup yet
  (everything is in-process Python bytes). Agreed direction: a live-I/O
  mode (output prints to real stdout immediately, input blocks on real
  stdin) plus a small CLI runner — planned for next session, see
  `docs/roadmap.md`'s "Planned follow-up" under Phase 2.

This is deliberately tiny — just enough to write "hello world" and read
queued input. Expand later if real programs need more (e.g. a timer,
multiple ports) rather than speculatively building more now.

## Clock / stepping model

For now, "the clock" is instruction-stepped, not cycle-accurate wall-clock
timed: each call to `cpu.step()` executes exactly one instruction and
returns the number of cycles it took. This is enough to:

- run programs correctly,
- track cycle counts for anyone who cares about timing,
- and, later, throttle a run loop to a target frequency if we ever want to
  simulate real-time behavior (e.g. for I/O timing).

True cycle-accurate mid-instruction stepping (matching real hardware bus
behavior tick by tick) is explicitly out of scope unless a specific need
comes up (e.g. supporting mid-instruction interrupt polling quirks) — see
`docs/hardware-path.md`.

## Calling convention (for the future C compiler, Phase 5)

The 6502's hardware stack (`$0100`-`$01FF`, addressed via `SP`) is only 256
bytes and is required for `JSR`/`RTS` and interrupt handling. It is **not**
usable as a general C call stack (no room for arguments/locals of arbitrary
size, and mixing them with return addresses is fragile).

Plan: implement a **software parameter/data stack** in RAM (see memory map
above), managed with two zero-page bytes as a 16-bbit stack pointer,
following the same approach used by real-world 6502 C compilers (e.g.
cc65). Function calls will still use `JSR`/`RTS` for the actual control
transfer; arguments, return values, and non-register-allocatable locals move
through the software stack. Exact calling convention (register vs. stack
args, how multi-byte `int` values are pushed/popped) is a Phase 5 decision —
revisit this section then.

## Status

The memory map, `Bus`, and `ConsoleDevice` above are implemented as
described (Phase 2, `src/c6502/emulator/bus.py`/`devices.py`) and match
this doc exactly — nothing diverged during implementation. The calling
convention section is still a plan, not yet implemented (that's Phase 5).
