"""Memory-mapped I/O devices.

ConsoleDevice is the minimal text console described in
docs/architecture.md: a write-only output register and a read-only input
register, attached into Bus's I/O window ($4000-$40FF in bus.py).
"""

from __future__ import annotations

from collections import deque
from typing import Union

OUTPUT_OFFSET = 0
INPUT_OFFSET = 1


class ConsoleDevice:
    """A tiny text console: write a byte, it becomes output; read a byte,
    get the next queued input (or 0 if none is waiting).
    """

    def __init__(self) -> None:
        self.output = bytearray()
        self._input: deque[int] = deque()

    def read8(self, offset: int) -> int:
        if offset == INPUT_OFFSET:
            return self._input.popleft() if self._input else 0
        return 0  # OUTPUT is write-only; any other sub-address reads as 0

    def write8(self, offset: int, value: int) -> None:
        if offset == OUTPUT_OFFSET:
            self.output.append(value & 0xFF)
        # Writes to INPUT or any other sub-address are simply ignored --
        # not every register needs both directions to mean something.

    def feed_input(self, data: Union[bytes, str]) -> None:
        """Queue bytes (or a str, encoded as ASCII) for a program to read
        back via the input register -- stands in for a keyboard/terminal.
        """
        if isinstance(data, str):
            data = data.encode("ascii")
        self._input.extend(data)

    @property
    def output_text(self) -> str:
        return self.output.decode("ascii", errors="replace")
