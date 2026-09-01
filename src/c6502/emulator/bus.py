"""Memory for the emulated system.

FlatMemory (a flat 64KB RAM) is what Phase 1's CPU-in-isolation tests run
against, and what Klaus Dormann's functional test suite wants too (Phase 3
-- it just needs contiguous writable RAM at a configurable address, not
our real memory map). Bus implements the actual system memory map from
docs/architecture.md: RAM, a read-only ROM region, and a memory-mapped I/O
window handed off to a device (see devices.py).
"""

from __future__ import annotations

from typing import Optional

from .devices import AciaDevice

IO_BASE = 0x4000
IO_SIZE = 0x0100
ROM_BASE = 0x8000
ROM_SIZE = 0x10000 - ROM_BASE


class ReadOnlyMemoryError(Exception):
    """Raised when the CPU tries to write to the ROM region.

    Real ROM chips just silently ignore writes -- we deliberately don't
    reproduce that here (unlike, say, the JMP-indirect page-wrap bug) since
    we're not aiming to run arbitrary buggy third-party ROMs; a write into
    ROM during our own development is far more likely a bug worth seeing
    loudly than something to shrug off.
    """

    def __init__(self, address: int) -> None:
        super().__init__(f"write to read-only ROM at ${address:04X}")
        self.address = address


class Bus:
    """The real system memory map: RAM + ROM + a memory-mapped I/O window."""

    def __init__(self, acia: Optional[AciaDevice] = None) -> None:
        self.ram = bytearray(ROM_BASE)  # backs $0000-$7FFF in full
        self.rom = bytearray(ROM_SIZE)  # $8000-$FFFF, incl. the vectors
        self.acia = acia if acia is not None else AciaDevice()

    def read8(self, address: int) -> int:
        address &= 0xFFFF
        if IO_BASE <= address < IO_BASE + IO_SIZE:
            return self.acia.read8(address - IO_BASE)
        if address < ROM_BASE:
            return self.ram[address]
        return self.rom[address - ROM_BASE]

    def write8(self, address: int, value: int) -> None:
        address &= 0xFFFF
        value &= 0xFF
        if IO_BASE <= address < IO_BASE + IO_SIZE:
            self.acia.write8(address - IO_BASE, value)
            return
        if address < ROM_BASE:
            self.ram[address] = value
            return
        raise ReadOnlyMemoryError(address)

    def read16(self, address: int) -> int:
        lo = self.read8(address)
        hi = self.read8((address + 1) & 0xFFFF)
        return lo | (hi << 8)

    def write16(self, address: int, value: int) -> None:
        self.write8(address, value & 0xFF)
        self.write8((address + 1) & 0xFFFF, (value >> 8) & 0xFF)

    def load_rom(self, data: bytes, origin: int = ROM_BASE) -> None:
        """Burn a program image into ROM, bypassing the read-only guard."""
        for offset, byte in enumerate(data):
            self.rom[(origin + offset) - ROM_BASE] = byte


class FlatMemory:
    """A flat block of RAM implementing the CPU's read8/write8 interface."""

    def __init__(self, size: int = 0x10000) -> None:
        self._data = bytearray(size)

    def read8(self, address: int) -> int:
        return self._data[address & 0xFFFF]

    def write8(self, address: int, value: int) -> None:
        self._data[address & 0xFFFF] = value & 0xFF

    def read16(self, address: int) -> int:
        lo = self.read8(address)
        hi = self.read8((address + 1) & 0xFFFF)
        return lo | (hi << 8)

    def write16(self, address: int, value: int) -> None:
        self.write8(address, value & 0xFF)
        self.write8((address + 1) & 0xFFFF, (value >> 8) & 0xFF)

    def load(self, address: int, data: bytes) -> None:
        for offset, byte in enumerate(data):
            self.write8(address + offset, byte)
