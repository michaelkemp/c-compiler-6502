"""Memory for the emulated system.

Phase 1 needs *something* the CPU can read/write bytes against; FlatMemory
(a flat 64KB RAM) is that something, and is real, reusable code -- not a
test-only stand-in. The full memory-mapped Bus described in
docs/architecture.md (RAM/ROM/IO regions, the console device) is Phase 2
and can wrap or extend this rather than being blocked on it.
"""

from __future__ import annotations


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
