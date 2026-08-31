from c6502.emulator.machine import Machine

# LDA #'H' / STA $4000 / LDA #'I' / STA $4000 / JMP <self>, loaded at $8000,
# with the reset vector pointing at $8000.
_PROGRAM_ORIGIN = 0x8000
_PROGRAM = bytes(
    [
        0xA9, ord("H"),        # LDA #'H'
        0x8D, 0x00, 0x40,      # STA $4000
        0xA9, ord("I"),        # LDA #'I'
        0x8D, 0x00, 0x40,      # STA $4000
        0x4C, 0x0A, 0x80,      # JMP $800A (self, infinite loop)
    ]
)


def _build_rom() -> bytes:
    rom = bytearray(0x8000)
    rom[: len(_PROGRAM)] = _PROGRAM
    reset_vector_offset = 0xFFFC - _PROGRAM_ORIGIN
    rom[reset_vector_offset] = _PROGRAM_ORIGIN & 0xFF
    rom[reset_vector_offset + 1] = (_PROGRAM_ORIGIN >> 8) & 0xFF
    return bytes(rom)


def test_machine_runs_hello_world_to_the_console():
    machine = Machine(_build_rom())
    assert machine.cpu.pc == _PROGRAM_ORIGIN  # reset picked up the vector

    machine.run(max_steps=8)  # 4 real instructions, then a few JMP-to-self spins

    assert machine.console.output_text == "HI"


def test_machine_run_returns_one_step_result_per_step():
    machine = Machine(_build_rom())
    results = machine.run(max_steps=4)
    assert [r.mnemonic for r in results] == ["LDA", "STA", "LDA", "STA"]
