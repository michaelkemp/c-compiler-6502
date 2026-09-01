"""Memory-mapped I/O devices.

AciaDevice models the real WDC W65C51N ACIA (Asynchronous Communications
Interface Adapter) -- the chip real 6502 hobbyist builds use for serial
I/O (see docs/architecture.md, docs/hardware-path.md). Register bit
semantics below are taken directly from WDC's official datasheet
(https://www.westerndesigncenter.com/wdc/documentation/w65c51n.pdf,
Status Register p.9, Command Register p.13-14), not guessed, so ROM code
written against this model behaves like it would against real hardware.

Attached into Bus's I/O window ($4000-$40FF in bus.py) at offsets 0-3:
    0  data register     (R: received byte: consumes it, clearing RDRF /
                           W: transmit a byte)
    1  status register    (R: see STATUS_* bit constants below /
                           W: "program reset" -- see _program_reset())
    2  command register   (R/W: see COMMAND_* bit constants below)
    3  control register    (R/W: stored but not otherwise modeled --
                           baud rate/word length are meaningless to a
                           software emulator)

Deliberately not modeled: parity/framing/overrun error generation, and
DSR/DCD as anything but a constant "ready"/"detected" -- there's no real
modem here to reflect, and matches how a hobbyist board wired directly to
a terminal (not through a modem) would tie those lines anyway.
"""

from __future__ import annotations

from collections import deque
from typing import Callable, Optional, Union

DATA_OFFSET = 0
STATUS_OFFSET = 1
COMMAND_OFFSET = 2
CONTROL_OFFSET = 3

# Status register bits (all as documented on the real chip; DSR/DCD/TDRE
# are constants here since we don't model a modem or transmit buffering).
STATUS_DSR_READY = 0  # bit 6 = 0 means "ready" on real hardware
STATUS_DCD_DETECTED = 0  # bit 5 = 0 means "detected"
STATUS_TDRE_EMPTY = 0x10  # bit 4: always empty/ready -- no transmit delay modeled
STATUS_RDRF = 0x08  # bit 3: a received byte is waiting
STATUS_IRQ = 0x80  # bit 7: an enabled interrupt condition is true

# Command register bits that we actually interpret (the rest -- echo
# mode, parity -- are stored for read-back but don't affect behavior).
COMMAND_DTR = 0x01  # bit 0: 1 = ready; also gates *all* interrupts (real
# hardware detail: "This bit enables all selected interrupts" per the
# datasheet -- easy to miss, so called out here explicitly).
COMMAND_RECEIVER_IRQ_DISABLE = 0x02  # bit 1: 1 = receiver interrupt disabled
COMMAND_PROGRAM_RESET_MASK = 0x0F  # bits 0-3 cleared by a "program reset"


class AciaDevice:
    def __init__(self, on_transmit: Optional[Callable[[int], None]] = None) -> None:
        self.output = bytearray()
        self._input: deque[int] = deque()
        self.command = 0
        self.control = 0
        self._on_transmit = on_transmit

    def read8(self, offset: int) -> int:
        if offset == DATA_OFFSET:
            return self._input.popleft() if self._input else 0
        if offset == STATUS_OFFSET:
            return self._status_byte()
        if offset == COMMAND_OFFSET:
            return self.command
        if offset == CONTROL_OFFSET:
            return self.control
        return 0

    def write8(self, offset: int, value: int) -> None:
        value &= 0xFF
        if offset == DATA_OFFSET:
            self.output.append(value)
            if self._on_transmit is not None:
                self._on_transmit(value)
        elif offset == STATUS_OFFSET:
            self._program_reset()
        elif offset == COMMAND_OFFSET:
            self.command = value
        elif offset == CONTROL_OFFSET:
            self.control = value

    def _status_byte(self) -> int:
        status = STATUS_TDRE_EMPTY
        if self._input:
            status |= STATUS_RDRF
        if self.irq_asserted:
            status |= STATUS_IRQ
        return status

    def _program_reset(self) -> None:
        # Real hardware also clears DTR/receiver-IRQ-disable/RTS bits in
        # the command register on a status-register write (per the
        # datasheet's own reset table) -- we don't generate parity/
        # framing/overrun errors in the first place, so there's nothing
        # else for a "reset" to clear on our model.
        self.command &= ~COMMAND_PROGRAM_RESET_MASK

    @property
    def irq_asserted(self) -> bool:
        ready = bool(self.command & COMMAND_DTR)
        receiver_irq_enabled = not (self.command & COMMAND_RECEIVER_IRQ_DISABLE)
        return ready and receiver_irq_enabled and bool(self._input)

    def feed_input(self, data: Union[bytes, str]) -> None:
        """Queue bytes (or a str, encoded as ASCII) for a program to read
        back via the data register -- stands in for a keyboard/terminal.
        """
        if isinstance(data, str):
            data = data.encode("ascii")
        self._input.extend(data)

    @property
    def output_text(self) -> str:
        return self.output.decode("ascii", errors="replace")
