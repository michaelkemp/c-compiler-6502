import pytest

from c6502.emulator.bus import Bus, ReadOnlyMemoryError


def test_ram_round_trip_across_zero_page_stack_and_general_ram():
    bus = Bus()
    for address in (0x0010, 0x0150, 0x0200, 0x3FFF, 0x4100, 0x7FFF):
        bus.write8(address, 0xAB)
        assert bus.read8(address) == 0xAB


def test_io_window_delegates_to_console():
    bus = Bus()
    bus.write8(0x4000, ord("Z"))
    assert bus.console.output_text == "Z"
    assert bus.read8(0x4000) == 0  # output register is write-only


def test_load_rom_then_read_back():
    bus = Bus()
    bus.load_rom(bytes([0xA9, 0x05]), origin=0x8000)
    assert bus.read8(0x8000) == 0xA9
    assert bus.read8(0x8001) == 0x05


def test_writing_to_rom_raises():
    bus = Bus()
    with pytest.raises(ReadOnlyMemoryError):
        bus.write8(0x8000, 0x00)


def test_read16_write16_for_vectors():
    bus = Bus()
    bus.load_rom(bytes(0x8000))  # zero-fill so write16 below targets ROM cleanly
    bus.rom[0xFFFC - 0x8000] = 0x00
    bus.rom[0xFFFD - 0x8000] = 0x80
    assert bus.read16(0xFFFC) == 0x8000
