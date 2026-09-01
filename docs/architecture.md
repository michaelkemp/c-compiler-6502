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

## Console I/O device (implemented: a real ACIA)

`src/c6502/emulator/devices.py`'s `AciaDevice` models the real **WDC
W65C51N ACIA**
([datasheet](https://www.westerndesigncenter.com/wdc/documentation/w65c51n.pdf))
at `$4000`-`$4003` within the `$4000`-`$40FF` I/O window — replacing an
earlier made-up 2-register protocol. Register bit meanings are taken
directly from the datasheet (Status Register p.9, Command Register
p.13-14), not guessed:

- `$4000` — **data register**: write to transmit a byte, read to receive
  one (reading pops the input queue, which also clears RDRF below — no
  separate acknowledgment step needed).
- `$4001` — **status register**: bit 7 = IRQ occurred, bit 6 = DSR (we
  always report `0`/ready — no real modem to reflect), bit 5 = DCD
  (always `0`/detected, same reason), bit 4 = TDRE (always `1` — we don't
  model transmit buffering/delay), bit 3 = RDRF (a byte is waiting), bits
  2-0 = overrun/framing/parity error (never set — we don't simulate line
  errors). Writing this register triggers a "program reset" (clears
  DTR/receiver-IRQ-disable/RTS in the command register), matching a real,
  slightly obscure chip behavior.
- `$4002` — **command register**: bit 0 = DTR (ready, and — a real,
  easy-to-miss detail from the datasheet — this bit gates *all*
  interrupts), bit 1 = receiver-IRQ-disable, bits 2-3 = RTS/transmit-IRQ
  control (per the datasheet, no combination on this real chip actually
  enables a transmit interrupt — a genuine W65C51N quirk we reproduce by
  simply never generating one), bits 4-7 = echo mode/parity (stored for
  read-back, not otherwise modeled).
- `$4003` — **control register**: stored but not otherwise modeled —
  baud rate/word length are meaningless to a software emulator.

`AciaDevice.irq_asserted` (`DTR and not receiver-IRQ-disabled and RDRF`)
feeds `Machine.step()`'s IRQ pump (`src/c6502/emulator/machine.py`),
which calls `cpu.irq()` before each instruction when true — `cpu.irq()`
already no-ops correctly if the CPU's `I` flag is set, so ROM code that
never does `CLI` stays purely polling-driven with this wired up.

Chosen over keeping the made-up protocol specifically because a ROM
written against a faithfully-modeled ACIA runs unmodified on real
hardware with a real W65C51N later — see `docs/hardware-path.md`.

## Live terminal attachment (implemented)

`src/c6502/run.py` (`python -m c6502.run <rom> [--origin ADDR] [--trace]`,
or the `c6502-run` console script) attaches a running `Machine`'s ACIA to
a real pseudo-terminal (`os.openpty()`) rather than this process's own
stdin/stdout, so an actual terminal program (`screen <path> 9600`,
`minicom`, PuTTY) can connect to it exactly as it would connect to real
hardware over a serial cable. The pty is put into **raw mode**
(`tty.setraw()`) — by default a pty is canonical/line-buffered, which
holds bytes written master→slave (our transmitted output) until a
newline instead of delivering them immediately; a real serial link has no
such buffering, so raw mode is what actually matches it. `run_interactive()`
non-blocking-polls the pty for input each step (never blocks the CPU loop
waiting for a keystroke, matching how a real ACIA just reports "not
ready" rather than halting the processor).

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

The memory map, `Bus`, `AciaDevice`, and the pty runner above are all
implemented and match this doc exactly. The calling convention section is
still a plan, not yet implemented (that's Phase 5).
