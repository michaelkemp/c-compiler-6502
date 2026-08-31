"""End-to-end proof: real assembly source -> assemble() -> Machine -> real
console output. Same shape as tests/emulator/test_machine.py's
hand-encoded "HI" program, but written and assembled from source this time.
"""

from c6502.asm import assemble
from c6502.emulator.machine import Machine

_SOURCE = """
    .org $8000
start:
    LDA #'H'
    STA $4000
    LDA #'I'
    STA $4000
loop:
    JMP loop

    .org $FFFC
    .word start
"""


def test_assembled_hello_world_runs_on_the_machine():
    image = assemble(_SOURCE)
    machine = Machine(image.data, rom_origin=image.origin)

    assert machine.cpu.pc == 0x8000  # reset vector picked up "start"

    machine.run(max_steps=8)  # 4 real instructions, then a few JMP-to-self spins

    assert machine.console.output_text == "HI"
