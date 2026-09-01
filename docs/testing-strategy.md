# Testing strategy

## Assembler (Phase 4)

Unit tests split by concern, same pattern as the CPU core:
`tests/asm/test_expr.py` (number/label expressions), `test_operands.py`
(addressing-mode detection), `test_directives.py`, `test_labels_and_branches.py`,
and an end-to-end `test_assemble_program.py` (assemble → `Machine` → real
console output).

Since the assembler can't consume Klaus Dormann's actual `.a65` source
(it uses macros/conditional assembly this minimal assembler doesn't
support), it's cross-checked against that suite two other ways instead:
`test_encoding_matches_cpu.py` proves every `(mnemonic, mode)` the
assembler can emit round-trips to the exact opcode byte the CPU decodes
(guaranteed by construction — `encoding.py` inverts the CPU's own
`OPCODES` table rather than duplicating it), and
`test_dormann_spot_check.py` reproduces the first 8 real instructions of
`6502_functional_test.bin` byte-for-byte from hand-written source in our
syntax.

## CPU core (Phase 1-3)

Two complementary layers:

1. **Klaus Dormann's 6502 functional test suite**
   ([github.com/Klaus2m5/6502_65C02_functional_tests](https://github.com/Klaus2m5/6502_65C02_functional_tests),
   **GPLv3-licensed** — this was previously (and incorrectly) described here
   as public domain; corrected in Phase 3 after actually reading
   `license.txt`) — exhaustively exercises every legal opcode and addressing
   mode combination plus flag behavior, and is the de facto standard
   correctness gate used by nearly every 6502 emulator project. It runs as
   a self-checking program that traps (jumps to itself) on both success and
   every failure — success traps at a specific known address (`$3469` for
   the pre-assembled binary below); any other trap address is a specific
   failing test, identifiable by grepping a fetched `.lst` listing for that
   address.
   - **Not vendored** in this repo, since it's GPLv3 and we'd rather not
     commit GPL-licensed content into our own git history. Run
     `scripts/fetch_dormann_tests.sh` once per machine to download the
     upstream repo's pre-assembled `6502_functional_test.bin` (a raw 64KB
     memory image — no assembler needed) into the gitignored
     `tests/emulator/fixtures/dormann/` directory.
   - The test itself (`tests/emulator/test_dormann_functional.py`) is
     marked `@pytest.mark.slow` (it's ~30M CPU steps, ~1-2 minutes) and
     excluded from the default `pytest` run via `addopts = "-m 'not slow'"`
     in `pyproject.toml`; run it explicitly with `pytest -m slow`. It
     `pytest.skip()`s with a pointer to the fetch script if the binary
     hasn't been downloaded, rather than failing the default suite.
   - It loads straight into `FlatMemory` and sets `cpu.pc` directly to the
     suite's configured entry point (`$400`) — no reset vector or real
     memory map involved (confirmed from the source: it just wants
     contiguous writable RAM at a few configurable addresses).
   - `6502_decimal_test` (BCD arithmetic) and `6502_interrupt_test`
     (IRQ/NMI) exist in the same repo but have **no pre-assembled binary**
     and would need real assembling (their source targets the old AS65
     assembler, not directly `ca65`-compatible) plus, for the interrupt
     test, a custom "feedback register" device to inject IRQ/NMI. Deferred
     as a non-blocking follow-up — see `docs/roadmap.md`. Note that the
     functional test binary already exercises decimal-mode ADC/SBC (its
     `disable_decimal` option defaults to enabled) and passes, so this
     isn't zero decimal-mode coverage even without the dedicated test.

2. **Hand-written unit tests** (pytest, under `tests/emulator/`) — smaller
   and faster, and useful for pinpointing exactly which instruction broke
   when the functional suite merely reports failure at some address. Write
   these alongside Phase 1 implementation, one instruction/addressing-mode
   family at a time, rather than only relying on the external suite.

## Real-world software: Microsoft BASIC

`tests/test_msbasic.py` (`@pytest.mark.slow`, same reasoning as the
Dormann test) boots real, unmodified Microsoft BASIC and runs a line of
it, asserting on the actual boot banner and computed output — the
strongest end-to-end proof available that the whole stack (CPU, `Bus`,
`AciaDevice`, `Machine`'s IRQ pump) is correct, since it's a real, 1977
program's own serial driver exercising all of it, not code we wrote to
test ourselves. Not vendored (same GPLv3-style caution as Dormann's suite
— see `scripts/fetch_msbasic.sh`'s comment); run
`scripts/fetch_msbasic.sh && scripts/build_msbasic.sh` once, then
`pytest -m slow`, same as Dormann's test.

## Compiler (Phase 5-6)

End-to-end style: a handful of small C sample programs (arithmetic, a loop,
a function call, array indexing) get compiled → assembled → run on the
emulator, with assertions on the emulator's console output or final memory
state — not just "did it compile" but "did it produce the right answer."

Add unit tests for the compiler's individual pieces (lexer, parser, codegen
for a single expression) as they're built, the same way as the CPU core.

## Status

CPU core: the functional test suite passes as of Phase 3 (traps at `$3469`
after 30,646,177 steps, ~80s in plain CPython); decimal/interrupt tests
deferred, see above. Assembler: done as of Phase 4, 126 fast tests total
across both. Real-world software: Microsoft BASIC boots and runs correctly
(see above). Compiler testing not started.
