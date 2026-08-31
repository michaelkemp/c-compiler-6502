"""6502 assembler.

Turns 6502 assembly source into a flat binary image (AssembledImage),
suitable for Bus.load_rom() (src/c6502/emulator/bus.py). See
docs/roadmap.md's Phase 4 plan for the supported syntax and the
deliberate "labels always assemble as absolute addressing" simplification.
This is the compiler's (cc/) future codegen target as well as a
standalone tool for hand-written asm.

Modules:
    expr.py      -- number/char literal parsing, label+offset expressions
    encoding.py  -- (mnemonic, mode) -> opcode byte, derived from
                    c6502.emulator.opcodes.OPCODES
    operands.py  -- operand syntax -> addressing mode
    assembler.py -- the two-pass driver: assemble(source) -> AssembledImage
"""

from .assembler import AssembledImage, assemble
from .errors import AssemblerError

__all__ = ["assemble", "AssembledImage", "AssemblerError"]
