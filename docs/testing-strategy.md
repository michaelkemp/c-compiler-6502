# Testing strategy

## CPU core (Phase 1-3)

Two complementary layers:

1. **Klaus Dormann's public-domain 6502 functional test suite**
   ([github.com/Klaus2m5/6502_65C02_functional_tests](https://github.com/Klaus2m5/6502_65C02_functional_tests)) —
   exhaustively exercises every legal opcode and addressing mode combination
   plus flag behavior, and is the de facto standard correctness gate used by
   nearly every 6502 emulator project. The suite runs as a self-checking
   program: it either loops forever at a well-known "success" address or
   traps at a "failure" address, so our test harness just needs to run it
   and assert which one it lands on.
   - Open question for Phase 3: how we obtain a runnable binary — assemble
     the `.a65` source ourselves (needs an assembler capable of its macros,
     which may be more than our own Phase 4 assembler supports at that
     point) vs. vendor a pre-assembled binary. Decide this when we get
     there.
   - There's also `6502_decimal_test` (BCD arithmetic) and
     `6502_interrupt_test` (IRQ/NMI) in the same repo — pull those in too
     once the basic functional test passes.

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

Not started — this describes the plan. Update as the actual test suite
takes shape.
