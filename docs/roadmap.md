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

### Follow-up: a real serial chip + live terminal I/O (done)

- [x] **Modeled the device after the real WDC W65C51N ACIA**
      ([datasheet](https://www.westerndesigncenter.com/wdc/documentation/w65c51n.pdf)) —
      `src/c6502/emulator/devices.py`'s `AciaDevice` (replacing the earlier
      made-up 2-register `ConsoleDevice`). Data/status/command/control
      registers with real bit semantics read from the datasheet, and
      IRQ-on-receive support wired into `Machine.step()` (finally giving
      the CPU's `cpu.irq()` a real caller beyond the hand-driven test in
      `tests/emulator/test_interrupts.py`).
- [x] **Attached to a real pseudo-terminal** — `src/c6502/run.py`
      (`python -m c6502.run <rom>`, or the `c6502-run` console script),
      using `os.openpty()` put into **raw mode** (`tty.setraw()`) so
      transmitted bytes aren't held up by the pty's default line
      buffering — a real gotcha hit and fixed this session (canonical
      mode holds master→slave writes until a newline; a real serial link
      has no such buffering).
- [x] Proof: a hand-written polling echo ROM (assembled with our own
      `c6502.asm`), tested via an in-process pty pair
      (`tests/test_run_cli.py`) and manually via a real subprocess +
      pty client round-trip.
- Rationale for chip realism: real 6502 builds (Ben Eater's included) use
  serial specifically because it's far simpler than faking a
  keyboard+display (see `docs/hardware-path.md`'s deferred bitmap-display
  note) — an actual W65C51N is inexpensive, real, and eliminates a whole
  layer of custom translation firmware an Arduino-bridge approach would
  otherwise need.
- A network/socket-based console, and an Arduino-as-protocol-bridge
  (rather than a real ACIA chip) were both considered and set aside.

### Follow-up: run real Microsoft BASIC (done)

Real, unmodified Microsoft BASIC (the actual 1977 interpreter, now
MIT-licensed by Microsoft) boots and runs programs on our emulator, over
our own `AciaDevice`:
```
MEMORY SIZE? [Enter]
TERMINAL WIDTH? [Enter]

15359 BYTES FREE

COPYRIGHT 1977 BY MICROSOFT CO.

OK
PRINT 1+1
 2

OK
```
- [x] **Platform files** (`msbasic/bios.s`, `defines_eater.s`, `eater.cfg`)
      — adapted from `beneater/msbasic` (a fork of `mist64/msbasic`
      already targeting a 6502 + serial ACIA, no video/keyboard hardware
      — much closer to our system than the raw Microsoft source, which
      targets a 1970s PDP-10 cross-assembler our own assembler can't
      parse). Changes from Ben's original: ACIA moved to `$4000` (ours)
      from `$5000` (his), `PHX`/`PLX` (65C02-only) replaced with an
      NMOS-safe stack+`Y` dance, VIA-based flow control removed (no VIA
      in our system), `RESET` jumps straight to `COLD_START` instead of
      into the WOZMON machine-code monitor first.
- [x] **A real bug found and fixed**: the first `PHX`/`PLX` replacement
      preserved `X` by bouncing it through `A`, but restored it *after*
      the character-to-return was already loaded into `A` — clobbering
      it. Root-caused via `ld65`'s `-Ln` label file (mapping the stuck PC
      back to `GETLN`/`MONRDKEY`), not by guessing from disassembly.
      Fixed properly using `Y` as scratch (free here; neither
      `BUFFER_SIZE` nor `READ_BUFFER` touch it) instead of a new
      zero-page byte — which would have silently collided with BASIC's
      own zero-page variables (`ZP_START0`-`ZP_START1` is exactly a
      2-byte gap already fully used by `READ_PTR`/`WRITE_PTR`).
- [x] `scripts/fetch_msbasic.sh` / `scripts/build_msbasic.sh` — fetch
      (pinned commit, not vendored — same GPLv3-style caution as Klaus
      Dormann's suite, since `mist64/msbasic`'s claimed 2-clause-BSD
      license has no actual `LICENSE` file backing it) + build via
      `ca65`/`ld65` (not our own assembler — this is exactly the kind of
      large third-party assembly project our Phase 4 assembler
      deliberately doesn't try to consume).
- [x] `tests/test_msbasic.py` (`@pytest.mark.slow`) + manual proof: ran
      the real `python -m c6502.run msbasic/build/msbasic.bin` CLI as a
      subprocess and talked to it through its pty exactly like a real
      terminal would.
- One cosmetic artifact, left as-is (authentic, not a bug): a stray "U"
  appears before "TERMINAL WIDTH?" — BASIC's own RAM-size auto-detection
  probes upward until a write/read-back test fails, and that probe lands
  on `$4000` (our ACIA) on its way to correctly stopping there; the $55
  ('U') test byte it writes gets "transmitted" as a side effect. Real
  hardware with memory-mapped I/O below the RAM ceiling has this same
  quirk.
- Not done (future, optional): WOZMON (the machine-code monitor) —
  skipped deliberately, not needed for this milestone.

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

## Phase 4 — Our own 6502 assembler (done)

- [x] Mnemonic + addressing-mode parsing — `src/c6502/asm/operands.py`.
      Opcode encoding (`encoding.py`) is derived by inverting
      `c6502.emulator.opcodes.OPCODES`, not a second hand-written table —
      guaranteed to never drift from what the CPU decodes (proven by
      `tests/asm/test_encoding_matches_cpu.py`).
- [x] Labels and forward references — two-pass assembly
      (`src/c6502/asm/assembler.py`), with a deliberate simplifying rule:
      a symbol (label or equate) used as an address operand always
      assembles as absolute addressing, even if its value would fit zero
      page (only a bare numeric/char literal gets the zero-page
      encoding). This avoids fixed-point-iteration sizing entirely — see
      the design note in `assembler.py`'s module docstring.
- [x] Directives: `.org`, `.byte`, `.word`, `.res` — plus a `name = expr`
      equate syntax (matches the `zero_page = $a` style seen in Klaus
      Dormann's source).
- [x] Emits a flat binary image (`AssembledImage(origin, data)`) — a
      direct drop-in for `Bus.load_rom()`.
- [x] End-to-end proof: assembled the same "HI" console program from
      Phase 2's hand-encoded test, now written as real assembly source,
      and ran it through `Machine` — `tests/asm/test_assemble_program.py`.
- [x] Cross-checked against Klaus Dormann's suite two ways (can't feed its
      actual `.a65` source through our assembler — it uses macros and
      conditional assembly this minimal assembler deliberately doesn't
      support): an opcode-table round-trip guarantee
      (`test_encoding_matches_cpu.py`) and a spot-check reproducing the
      first 8 real instructions of `6502_functional_test.bin` byte-for-byte
      (`test_dormann_spot_check.py`).

Deferred, non-blocking: macros, `.include`, multiple named segments,
low/high-byte operators (`<`/`>`), auto-shrinking forward references to
zero page. Would be needed to fully reassemble Dormann's suite ourselves,
but not for the small programs Phase 5/6 generate.

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

- [x] Document what would need to change to run on real hardware (timing
      fidelity, a real I/O chip instead of a toy MMIO device, level
      shifting/bus considerations) — `docs/hardware-path.md`
- [x] Flag which Phase 1–6 design choices already anticipate this vs. would
      need rework — same doc; the ACIA (Phase 2 follow-up) and the
      assembler's flat binary output (Phase 4) both already anticipated it
- [x] **A real, staged build plan** — `docs/hardware-build.md`: Stage 1
      (CPU + RAM + ROM + clock + reset bring-up) fully detailed with a
      real parts list (sourced, with links), verified pin-accurate wiring
      (datasheets fetched via `scripts/fetch_datasheets.sh`, not vendored
      — same reasoning as Dormann's suite/msbasic), a circuit diagram
      (`docs/hardware/stage1-schematic.svg`), and a bring-up test program
      using our own assembler. Stages 2 (serial console) and 3 (VGA/PS2
      via a Pico coprocessor) are outlined, to be detailed when we get
      there.
- [ ] **Known deviation from the emulator's target, decided deliberately**:
      the real build uses a **WDC W65C02S**, not an original NMOS 6502 —
      new-production availability/reliability won out over exact fidelity
      to what the emulator models (genuine NMOS 6502 dies are decades-old
      surplus stock at this point). Software built against our NMOS-only
      emulator should still run correctly (the 65C02 is a superset for
      documented, legal opcodes), but this is worth remembering if
      real-hardware behavior and the emulator's ever disagree on an edge
      case — the 65C02 fixed a few NMOS quirks we deliberately reproduce
      in software (e.g. the `JMP (indirect)` page-wrap bug in
      `docs/6502-reference.md`).
