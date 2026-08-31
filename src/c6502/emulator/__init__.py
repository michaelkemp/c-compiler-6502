"""NMOS 6502 CPU emulator and minimal system harness.

Implemented (Phase 1): cpu.py (CPU/Flags/StepResult), bus.py (FlatMemory),
addressing.py, instructions.py, opcodes.py (the OPCODES dispatch table),
trace.py (step trace line formatting).

Planned (Phase 2, not yet implemented): devices.py -- memory-mapped I/O
devices, and a real memory-mapped Bus per docs/architecture.md wrapping
FlatMemory's RAM region alongside ROM and I/O.
"""
