# c-compiler-6502

A software 6502 emulator, assembler, and (eventually) C compiler, built up
from the CPU itself. See [CLAUDE.md](CLAUDE.md) for the full goals,
architecture decisions, and phase-by-phase status.

## The 30-second version of why this is cool

This repo emulates a real MOS 6502 CPU precisely enough that **real,
unmodified Microsoft BASIC from 1977** boots and runs on it, talking over
a real ACIA serial chip model, connected to an actual terminal program on
your machine — the same experience as a real 6502 hobbyist board, entirely
in software.

## Try it: real Microsoft BASIC over a serial terminal

**Requirements**: Python 3.11+, and `ca65`/`ld65` (part of the `cc65`
toolchain) to build BASIC — e.g. `sudo apt install cc65` on
Debian/Ubuntu, `brew install cc65` on macOS.

```
git clone <this repo>
cd c-compiler-6502
python3 -m venv .venv
.venv/bin/pip install -e .

scripts/fetch_msbasic.sh    # fetches Microsoft BASIC source (not vendored, see below)
scripts/build_msbasic.sh    # builds it for our system with ca65/ld65

.venv/bin/python -m c6502.run msbasic/build/msbasic.bin
```

That last command starts the emulator and prints something like:

```
Listening on /dev/pts/6
Connect with: screen /dev/pts/6 9600
```

**In a second terminal window**, run the exact `screen ...` command it
printed (the path/number will differ each time — use whatever it actually
printed, not the example above). You should see:

```
MEMORY SIZE? [press Enter]
TERMINAL WIDTH? [press Enter]

15359 BYTES FREE

COPYRIGHT 1977 BY MICROSOFT CO.

OK
```

Now type a line of BASIC and press Enter:

```
PRINT 1+1
```
```
 2

OK
```

You're now running real, 1977 Microsoft BASIC — the same interpreter
licensed to Apple, Commodore, and dozens of other early microcomputers —
on a 6502 CPU emulated from scratch in this repo, over a serial port
model built from the real chip's datasheet. Write and run a whole
program, not just one line — line numbers, `GOTO`, `FOR`/`NEXT`, all of
it works.

Don't have `screen`? `minicom` or `picocom` work the same way, connecting
to the same path at any baud rate (it's a virtual pty, not a real serial
line, so the baud number doesn't actually matter).

To stop the emulator, go back to the first terminal and press Ctrl+C.

## Running the test suite

```
.venv/bin/pytest
```

See [CLAUDE.md](CLAUDE.md#running-tests) for the full details (no venv
is strictly required, decimal test suite notes, etc.) and how to also run
the slower validation tests (Klaus Dormann's 6502 functional test suite,
and an automated version of the Microsoft BASIC boot-and-run demo above).

## What's actually in this repo

- `src/c6502/emulator/` — the 6502 CPU core, memory bus, and the ACIA
  serial chip model
- `src/c6502/asm/` — our own 6502 assembler
- `src/c6502/run.py` — the CLI used above, attaching a running machine to
  a real terminal
- `msbasic/` — our platform-specific glue for running Microsoft BASIC
  (the BASIC source itself is fetched on demand, not vendored — see
  `scripts/fetch_msbasic.sh`'s comments for why)
- `docs/` — architecture, ISA reference, and testing strategy notes

Full status and what's next: [CLAUDE.md](CLAUDE.md).
