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

Known gaps, updated now that Phase 3's functional suite is wired up:
- Decimal-mode (`D` flag) `ADC`/`SBC` flag behavior (N/V/Z/C) is a
  best-effort implementation of the commonly documented NMOS algorithm —
  see the comments in `instructions.py`'s `_adc_decimal`/`_sbc_decimal`.
  Passing the functional test suite (which exercises decimal mode by
  default) is a real signal this is at least mostly right, but it's still
  not cross-checked bit-for-bit against Dormann's dedicated, exhaustive
  decimal test, which remains deferred (see Phase 3 below).
- `IRQ`/`NMI` are implemented as immediate register-level push/jump; no
  attempt yet at cycle-by-cycle interrupt-polling timing (e.g. exactly
  which instruction boundary an interrupt is recognized at) — flagged in
  `docs/hardware-path.md` as a timing-fidelity gap, and not covered by the
  functional suite either (that needs the separate, also-deferred
  interrupt test).

## Phase 2 — Minimal system harness (done)

- [x] `Bus` implementing our memory map (see `docs/architecture.md`) —
      `src/c6502/emulator/bus.py`. `FlatMemory` (Phase 1) is unchanged and
      still what Phase 3's Klaus Dormann suite will run against.
- [x] RAM region — one `bytearray` backing `$0000`-`$7FFF` (zero page,
      hardware stack, general RAM, and the still-reserved `$4100`-`$7FFF`
      all live in it)
- [x] ROM region, loadable via `Bus.load_rom()` — read-only from the CPU's
      normal write path (`ReadOnlyMemoryError` on a write attempt; a
      deliberate emulator convention, not a claim about real ROM chips —
      see the comment in `bus.py`)
- [x] A minimal memory-mapped text console (`$4000` output / `$4001`
      input) — `src/c6502/emulator/devices.py`'s `ConsoleDevice`. Confirmed
      text-console over a Nand2Tetris-style bitmap framebuffer this
      session — see `docs/hardware-path.md`.
- [x] A step/run loop standing in for "the clock" — `Machine.run()` in
      `src/c6502/emulator/machine.py`, bounded by a `max_steps` count since
      there's no halt-detection convention yet (a Phase 3/6 concern)
- [x] End-to-end proof: a hand-assembled "HI" program loaded into ROM,
      run through `Machine`, producing `console.output_text == "HI"` —
      `tests/emulator/test_machine.py`

## Phase 3 — Validation (functional suite done; decimal/interrupt deferred)

- [x] Obtain Klaus Dormann's functional test suite in a runnable form —
      it's GPLv3 (corrected from an earlier, wrong "public domain" claim in
      this repo's docs), so it's fetched on demand rather than vendored:
      `scripts/fetch_dormann_tests.sh` downloads the upstream repo's
      pre-assembled `6502_functional_test.bin` into the gitignored
      `tests/emulator/fixtures/dormann/`
- [x] Load + run it against the emulator; assert it reaches the suite's
      success trap (`$3469`) rather than a failure trap —
      `tests/emulator/test_dormann_functional.py`, marked `@pytest.mark.slow`
      (excluded from the default `pytest` run; opt in with `pytest -m slow`).
      **Passes**: traps at `$3469` after 30,646,177 steps (~80s).
- [x] Hand-written unit tests for individual opcodes/addressing
      modes/flags as a complement — done in Phase 1 (66 tests) plus Phase 2
      (12 more), for 78 total in the default fast suite.
- [ ] Deferred, non-blocking: `6502_decimal_test.a65` and
      `6502_interrupt_test.a65` have no pre-assembled binary in the
      upstream repo (unlike the functional test) and would need real
      assembling (their source targets the old AS65 assembler, not
      directly `ca65`-compatible, though `ca65`/`ld65` are installed
      locally) plus, for the interrupt test, a custom "feedback register"
      I/O device to inject IRQ/NMI. The functional test binary already
      exercises decimal-mode ADC/SBC and passed, so this isn't zero
      decimal-mode coverage even without the dedicated test — see
      `docs/testing-strategy.md`.

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
