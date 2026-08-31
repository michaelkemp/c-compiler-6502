"""6502 assembler (Phase 4 -- not yet implemented).

Will parse mnemonics + addressing modes, resolve labels, support the
directives listed in docs/roadmap.md (.org, .byte, .word, .res), and emit a
flat binary image at a given load address. This is the compiler's codegen
target (see cc/) as well as a standalone tool for hand-written asm.
"""
