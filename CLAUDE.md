# c-compiler-6502

## Goal

Build, in this repo, a small but *real* computer stack from the CPU up:

1. A software emulator for the **MOS 6502** CPU, written in Python.
2. A simple computer around it: RAM, ROM, a clock/step loop, and basic
   memory-mapped I/O.
3. An assembler for 6502 machine code.
4. A C compiler that targets that assembler, starting from a small subset of
   C and growing over time.
5. A documented path toward running the same software on real hardware (a
   real 6502, real RAM, and something like an Arduino bridging I/O) — not
   necessarily built in this repo, but the design should not paint us into a
   corner where it's impossible.

The motivation: after finishing the Nand2Tetris course, the "Hack" computer
built there wasn't powerful enough to run even the course's own OS. This
project aims for something with a lower ceiling to hit — the 6502 is a real,
historically significant CPU (Apple I/II, Commodore 64, NES, BBC Micro) with
decades of documentation, real software, and real hardware behind it.

**This file is the living source of truth**: goals, architecture decisions,
and current status. Detail lives in [docs/](docs/); update both as decisions
change.

## Architecture decisions

- **CPU target: original NMOS 6502**, not 65C02. Matches the most
  historically significant machines and the widest body of reference
  material and test suites. See [docs/6502-reference.md](docs/6502-reference.md).
- **Memory map: custom**, designed by us rather than copied from an existing
  board (e.g. Ben Eater's). See [docs/architecture.md](docs/architecture.md)
  for the current layout.
- **Calling convention**: the 6502's hardware stack is only 256 bytes and is
  needed for `JSR`/`RTS`/interrupts, so it's not usable as a C call stack.
  The compiler will use a **software parameter/data stack in RAM** instead —
  the standard technique used by real-world 6502 C compilers (e.g. cc65).
  Details in [docs/architecture.md](docs/architecture.md).
- **Repo layout: a single installable Python package** (`c6502`) with
  submodules for the emulator, assembler, and compiler, rather than separate
  top-level projects — this keeps end-to-end tests (C → asm → emulator)
  straightforward.
- **CPU correctness testing**: validated against Klaus Dormann's 6502
  functional test suite (GPLv3 — fetched on demand, not vendored, see
  `scripts/fetch_dormann_tests.sh`), plus our own unit tests. See
  [docs/testing-strategy.md](docs/testing-strategy.md).
- **C compiler v1 scope**: a tiny arithmetic/control-flow subset first,
  grown incrementally. See [docs/c-subset.md](docs/c-subset.md).

## Repo map

```
CLAUDE.md              # this file
pyproject.toml         # package metadata, dev dependencies (pytest)
docs/
  roadmap.md           # phase checklist / detailed status tracker
  6502-reference.md    # our condensed 6502 ISA notes + links to full references
  architecture.md      # memory map, I/O device, clock model, calling convention
  c-subset.md          # target C grammar for the compiler, phase by phase
  hardware-path.md     # notes on moving from emulator to real hardware
  testing-strategy.md  # how the emulator and (later) compiler get validated
src/c6502/
  emulator/            # CPU core, bus/memory, opcode table, I/O devices
  asm/                 # our own 6502 assembler
  cc/                  # the C compiler front end and 6502 codegen
tests/
  emulator/            # tests for the CPU core and system harness
```

## Status / roadmap

See [docs/roadmap.md](docs/roadmap.md) for the detailed phase checklist.
Summary:

- [x] **Phase 0** — docs + package scaffolding
- [x] **Phase 1** — CPU core (registers, flags, all legal addressing modes,
      151-entry opcode dispatch table, cycle counting, reset/IRQ/NMI/BRK,
      a step trace formatter, 66 pytest tests) — see `docs/roadmap.md` for
      the known gaps left for Phase 3 (decimal-mode flag exactness,
      interrupt timing fidelity)
- [x] **Phase 2** — minimal system harness: a real memory-mapped `Bus`
      (RAM/ROM/IO regions per `docs/architecture.md`), an `AciaDevice`
      modeling the real WDC W65C51N serial chip (register semantics from
      its datasheet, not guessed; replaced an earlier made-up protocol —
      confirmed over a bitmap framebuffer, see `docs/hardware-path.md`),
      and a `Machine` wrapper with a step/run loop + IRQ pump. Attached to
      a real pseudo-terminal in raw mode (`src/c6502/run.py`,
      `python -m c6502.run` / `c6502-run`), so a real terminal program can
      connect to it like real hardware over a serial cable. End-to-end
      verified with a hand-assembled/hand-assembled-via-our-own-assembler
      polling echo program, both automated (in-process pty pair) and live
      (a real subprocess + pty client round-trip).
- [x] **Follow-up to Phase 2** — real, unmodified **Microsoft BASIC**
      (the actual 1977 interpreter, now MIT-licensed) boots and runs
      programs on our emulator over the real ACIA (`msbasic/`,
      `scripts/fetch_msbasic.sh` + `build_msbasic.sh`, not vendored — see
      `docs/roadmap.md`). Found and fixed a real bug along the way (an
      NMOS replacement for a 65C02-only instruction pair was clobbering
      the character it was supposed to return).
- [x] **Phase 3** — validated the CPU core against Klaus Dormann's
      functional test suite: **passes**, trapping at the documented success
      address (`$3469`) after 30,646,177 steps (~80s). Not vendored (it's
      GPLv3, corrected from an earlier wrong "public domain" claim in this
      file) — fetched on demand via `scripts/fetch_dormann_tests.sh` into a
      gitignored fixture, and run via `pytest -m slow` (excluded from the
      default fast suite). Decimal/interrupt sub-tests deferred — see
      `docs/roadmap.md`.
- [x] **Phase 4** — our own 6502 assembler (`src/c6502/asm/`): mnemonic +
      addressing-mode parsing, two-pass label/forward-reference support,
      `.org`/`.byte`/`.word`/`.res` + equates, emitting a flat binary image
      that drops straight into `Bus.load_rom()`. Its opcode encoding is
      derived by inverting the CPU's own `OPCODES` table, so it can never
      drift from what the CPU decodes. Verified end-to-end (assembled "HI"
      program running on `Machine`) and cross-checked against real
      Dormann-suite bytes (see `docs/roadmap.md`).
- [ ] **Phase 5** — tiny-C compiler v1
- [ ] **Phase 6** — end-to-end integration (C → asm → emulator)
- [ ] **Phase 7** — hardware-path design notes

`src/c6502/emulator/{cpu,bus,addressing,instructions,opcodes,trace,
devices,machine}.py`, `src/c6502/asm/{expr,encoding,operands,
assembler}.py`, and `src/c6502/run.py` (the pty-attached CLI runner) are
implemented and tested (136 fast tests + 2 slow tests: the Dormann suite
and Microsoft BASIC boot/run). `src/c6502/cc/*` is still a stub for
Phase 5.

## Reference documentation

Our own notes: everything under [docs/](docs/).

External sources of truth (linked rather than copied wholesale, for license
cleanliness — pull specific facts as needed rather than bulk-copying):

- 6502 opcode / addressing-mode reference:
  [masswerk.at/6502/6502_instruction_set.html](https://masswerk.at/6502/6502_instruction_set.html)
- General 6502 knowledge base, tutorials, forum:
  [6502.org](https://6502.org)
- Klaus Dormann's 6502/65C02 functional test suite (GPLv3; used as our
  emulator correctness gate, fetched on demand rather than vendored — see
  `scripts/fetch_dormann_tests.sh` and `docs/testing-strategy.md`):
  [github.com/Klaus2m5/6502_65C02_functional_tests](https://github.com/Klaus2m5/6502_65C02_functional_tests)
- WDC W65C51N ACIA datasheet (real serial chip our `AciaDevice` models):
  [westerndesigncenter.com/wdc/documentation/w65c51n.pdf](https://www.westerndesigncenter.com/wdc/documentation/w65c51n.pdf)
- `beneater/msbasic` (fork of `mist64/msbasic`, a modernized,
  `ca65`-buildable port of Microsoft's now-MIT-licensed original 6502
  BASIC, already targeting a 6502 + serial ACIA; pinned commit, fetched
  on demand rather than vendored — see `scripts/fetch_msbasic.sh` and
  `docs/roadmap.md`): [github.com/beneater/msbasic](https://github.com/beneater/msbasic)

## Running tests

No compiled/native dependencies and no runtime dependencies at all
(`dependencies = []` in `pyproject.toml`) -- the only thing you need is
Python 3.11+ and `pytest` itself. `pyproject.toml` sets `pythonpath =
["src"]`, so pytest finds the `c6502` package directly from the source
tree; you do **not** need to `pip install` this package (editable or
otherwise) just to run the tests.

Quickest path, if `pytest` is already available on your system (via your
OS package manager, `pipx`, etc.):
```
pytest
```

Otherwise, isolate it in a venv (recommended, and the only option on
distros that block plain `pip install` outside one, e.g. Debian/Ubuntu's
PEP 668 "externally managed environment"):
```
python3 -m venv .venv
.venv/bin/pip install pytest
.venv/bin/pytest
```

`pip install -e ".[dev]"` still works and is worth doing once you're
building the assembler/compiler and want `import c6502` to work from a
plain `python3` shell too, but it's not required just to run the test
suite.

Plain `pytest` only runs the fast suite (~0.1s). To also run the slow
tests (Klaus Dormann's functional suite, ~80s, and Microsoft BASIC
boot/run, ~15s; neither runs by default):
```
scripts/fetch_dormann_tests.sh    # one-time per machine, fetches a GPLv3
                                   # binary into a gitignored fixture dir
scripts/fetch_msbasic.sh          # one-time per machine, fetches (pinned
scripts/build_msbasic.sh          # commit, not vendored) + builds BASIC
pytest -m slow
```
