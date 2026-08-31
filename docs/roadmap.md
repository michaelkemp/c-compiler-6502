# Roadmap / status

Detailed phase checklist for the project. Keep this file up to date as work
progresses — it's the answer to "where are we up to?" CLAUDE.md links here
and carries only the summary.

## Phase 0 — Docs + scaffolding (done)

- [x] `CLAUDE.md` written
- [x] `docs/` reference tree written
- [x] `src/c6502/` package skeleton with stub modules
- [x] `pyproject.toml` with package metadata + pytest dev dependency

## Phase 1 — CPU core (done)

- [x] Registers: A, X, Y, SP, PC, status (P) flags (N V - B D I Z C)
      (`src/c6502/emulator/cpu.py`: `CPU`, `Flags`)
- [x] All legal NMOS 6502 addressing modes (implied, accumulator, immediate,
      zero page [,X/,Y], absolute [,X/,Y], indirect, indexed indirect,
      indirect indexed, relative) — `src/c6502/emulator/addressing.py`,
      including the `JMP (indirect)` page-wrap bug reproduced deliberately
- [x] Data-driven opcode dispatch table covering all 151 legal opcode
      encodings — `src/c6502/emulator/opcodes.py` (semantics in
      `instructions.py`)
- [x] Cycle counting per instruction (incl. page-cross / branch-taken
      penalties) — returned on `StepResult.cycles`
- [x] Reset / IRQ / NMI / BRK / RTI vector handling — `CPU.reset()`,
      `CPU.irq()`, `CPU.nmi()`
- [x] Illegal/undocumented opcodes raise `IllegalOpcodeError` rather than
      silently misbehaving, per the decision above
- [x] Simple trace log — `src/c6502/emulator/trace.py`'s `format_step()`
- [x] Incremental pytest suite per instruction family —
      `tests/emulator/test_*.py` (66 tests)

Known gaps to revisit once Klaus Dormann's suite is wired up in Phase 3:
- Decimal-mode (`D` flag) `ADC`/`SBC` flag behavior (N/V/Z/C) is a
  best-effort implementation of the commonly documented NMOS algorithm, not
  yet cross-checked bit-for-bit against Dormann's dedicated decimal test —
  see the comments in `instructions.py`'s `_adc_decimal`/`_sbc_decimal`.
- `IRQ`/`NMI` are implemented as immediate register-level push/jump; no
  attempt yet at cycle-by-cycle interrupt-polling timing (e.g. exactly
  which instruction boundary an interrupt is recognized at) — flagged in
  `docs/hardware-path.md` as a timing-fidelity gap.

## Phase 2 — Minimal system harness

- [ ] `Bus`/`Memory` abstraction implementing our memory map
      (see `docs/architecture.md`)
- [ ] RAM region
- [ ] ROM region (loadable from a binary image)
- [ ] A minimal memory-mapped console I/O device (write a byte → appears as
      output; a status/data register pair for input)
- [ ] A step/run loop standing in for "the clock" (instruction-stepped for
      now; cycle-accurate timing is not a goal yet)

## Phase 3 — Validation

- [ ] Obtain Klaus Dormann's functional test suite in a runnable form
      (decide: vendor a pre-assembled binary vs. assemble the `.a65` source
      ourselves with an external assembler used only for this)
- [ ] Load + run it against the emulator; assert it reaches the suite's
      defined "success" trap rather than a "failure" trap
- [ ] Hand-written unit tests for individual opcodes/addressing modes/flags
      as a complement (useful for pinpointing failures the functional suite
      only reports in aggregate)

## Phase 4 — Our own 6502 assembler

- [ ] Mnemonic + addressing-mode parsing
- [ ] Labels and forward references
- [ ] Directives: `.org`, `.byte`, `.word`, `.res` (reserve space)
- [ ] Emits a flat binary image at a given load address

## Phase 5 — Tiny-C compiler v1

See `docs/c-subset.md` for the exact grammar target. High level:

- [ ] Lexer + parser → AST for the subset
- [ ] `int` (16-bit) and `char` (8-bit) types; globals and locals
- [ ] Functions with parameters and return values via a software
      parameter/data stack
- [ ] Operators: `+ - * / %`, comparisons, `&& || !`, assignment
- [ ] Control flow: `if`/`else`, `while`, `for`
- [ ] Single-level pointers and one-dimensional arrays
- [ ] Codegen emits assembly for our own assembler (Phase 4)

## Phase 6 — End-to-end integration

- [ ] A handful of small C sample programs (arithmetic, loops, a function
      call, array indexing) compiled → assembled → run on the emulator
- [ ] Assertions on emulated console output / final memory state

## Phase 7 — Hardware-path design notes

- [ ] Document what would need to change to run on a real NMOS 6502 + RAM
      + Arduino-bridged I/O (timing fidelity, a real I/O chip instead of our
      toy MMIO device, level shifting/bus considerations)
- [ ] Flag which Phase 1–6 design choices already anticipate this vs. would
      need rework
