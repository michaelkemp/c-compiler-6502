"""NMOS 6502 CPU emulator and minimal system harness.

Implemented (Phase 1): cpu.py (CPU/Flags/StepResult), addressing.py,
instructions.py, opcodes.py (the OPCODES dispatch table), trace.py (step
trace line formatting).

Implemented (Phase 2): bus.py (FlatMemory -- a flat 64KB RAM for
CPU-in-isolation testing and Phase 3's Klaus Dormann suite -- and Bus, the
real memory-mapped RAM/ROM/IO system per docs/architecture.md),
machine.py (Machine, wiring CPU+Bus+AciaDevice together with a step/run
loop, incl. pumping IRQs from the ACIA into the CPU).

Implemented (this session): devices.py's AciaDevice models the real WDC
W65C51N serial chip (replacing an earlier made-up 2-register protocol),
and run.py (top-level, not under emulator/) attaches it to a real
pseudo-terminal so an actual terminal program can connect to a running
Machine.
"""
