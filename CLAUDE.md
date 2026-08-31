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
- **CPU correctness testing**: validated against Klaus Dormann's public
  domain 6502 functional test suite, plus our own unit tests. See
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
      (RAM/ROM/IO regions per `docs/architecture.md`), a text `ConsoleDevice`
      (confirmed over a bitmap framebuffer — see `docs/hardware-path.md`),
      and a `Machine` wrapper with a step/run loop. End-to-end verified with
      a hand-assembled program producing real console output.
- [ ] **Phase 3** — validate the CPU core against Klaus Dormann's functional
      test suite (confirmed independent of Phase 2 — the suite just wants
      contiguous writable RAM, so it runs against `FlatMemory`)
- [ ] **Phase 4** — our own 6502 assembler
- [ ] **Phase 5** — tiny-C compiler v1
- [ ] **Phase 6** — end-to-end integration (C → asm → emulator)
- [ ] **Phase 7** — hardware-path design notes

`src/c6502/emulator/{cpu,bus,addressing,instructions,opcodes,trace,
devices,machine}.py` are implemented and tested. `src/c6502/asm/*` and
`src/c6502/cc/*` are still stubs for Phases 4 and 5.

## Reference documentation

Our own notes: everything under [docs/](docs/).

External sources of truth (linked rather than copied wholesale, for license
cleanliness — pull specific facts as needed rather than bulk-copying):

- 6502 opcode / addressing-mode reference:
  [masswerk.at/6502/6502_instruction_set.html](https://masswerk.at/6502/6502_instruction_set.html)
- General 6502 knowledge base, tutorials, forum:
  [6502.org](https://6502.org)
- Klaus Dormann's public-domain 6502/65C02 functional test suite (used as
  our emulator correctness gate):
  [github.com/Klaus2m5/6502_65C02_functional_tests](https://github.com/Klaus2m5/6502_65C02_functional_tests)

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
