"""NMOS 6502 CPU emulator and minimal system harness.

Implemented (Phase 1): cpu.py (CPU/Flags/StepResult), addressing.py,
instructions.py, opcodes.py (the OPCODES dispatch table), trace.py (step
trace line formatting).

Implemented (Phase 2): bus.py (FlatMemory -- a flat 64KB RAM for
CPU-in-isolation testing and Phase 3's Klaus Dormann suite -- and Bus, the
real memory-mapped RAM/ROM/IO system per docs/architecture.md),
devices.py (ConsoleDevice, the text-console I/O device), machine.py
(Machine, wiring CPU+Bus+ConsoleDevice together with a step/run loop).
"""
