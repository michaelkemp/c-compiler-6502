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

## Console I/O device

Currently implemented (Phase 2): a minimal, made-up 2-register device at
`$4000`-`$4001` (`src/c6502/emulator/devices.py`'s `ConsoleDevice`) — write
`$4000` to output a byte, read `$4001` to consume a queued input byte
(`console.feed_input(...)` supplies it; no live stdin/stdout hookup, and
no resemblance to any real chip).

**Planned to replace this** (see `docs/roadmap.md`'s "Planned follow-up"
under Phase 2, decided in a design session): model the device instead
after the real **WDC W65C51N ACIA**
([datasheet](https://www.westerndesigncenter.com/wdc/documentation/w65c51n.pdf)),
still within the same `$4000`-`$40FF` I/O window:

- `$4000` — **data register**: write to transmit a byte, read to receive one.
- `$4001` — **status register**: bit 0 = receive-data-ready, bit 1 =
  transmit-data-empty, bit 7 = an IRQ occurred — polled or, with IRQs
  enabled, used with `cpu.irq()` (already implemented since Phase 1, not
  yet used by anything) so the CPU is interrupted on receipt instead of
  having to poll.
- `$4002` — **command register**: IRQ enable/disable, among other real
  ACIA options we likely won't need to model exactly.
- `$4003` — **control register**: baud rate / word length — mostly
  irrelevant to a software emulator, but real on hardware.

Chosen over keeping the made-up protocol specifically because a ROM
written against a faithfully-modeled ACIA runs unmodified on real
hardware with a real W65C51N later — see `docs/hardware-path.md`. Also
planned: attaching this to a real pseudo-terminal (Python's `pty` module)
rather than this process's own stdin/stdout, so an actual terminal
program can connect to the running emulator the way it would connect to
real hardware over a serial cable.

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

The memory map and `Bus` are implemented as described (Phase 2,
`src/c6502/emulator/bus.py`) and match this doc exactly. `ConsoleDevice`
(`devices.py`) currently implements the made-up 2-register protocol, not
yet the planned ACIA-shaped one described above — that's next session's
work. The calling convention section is still a plan, not yet implemented
(that's Phase 5).
