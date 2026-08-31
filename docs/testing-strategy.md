# Testing strategy

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
deferred, see above. Compiler testing not started.
