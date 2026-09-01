"""Proves the pty-attached CLI runner works end to end without needing a
real terminal program or a subprocess: open a pty pair ourselves, write
into the *follower* fd (simulating what a connected terminal would send),
run the interactive loop synchronously (bounded by max_steps), and read
back what came out the follower fd.
"""

import os
import tty

from c6502.asm import assemble
from c6502.emulator.machine import Machine
from c6502.run import run_interactive

_ECHO_SOURCE = """
    .org $8000
reset:
    LDA #$09        ; DTR=1, receiver IRQ enabled, RTS low, no parity
    STA $4002
loop:
    LDA $4001       ; status register
    AND #$08        ; RDRF?
    BEQ loop
    LDA $4000       ; read the received byte (clears RDRF)
    STA $4000       ; echo it straight back
    JMP loop
    .org $FFFC
    .word reset
"""


def _build_echo_machine(controller_fd: int) -> Machine:
    image = assemble(_ECHO_SOURCE)
    return Machine(
        image.data,
        rom_origin=image.origin,
        on_transmit=lambda byte: os.write(controller_fd, bytes([byte])),
    )


def test_echo_rom_round_trips_through_a_real_pty():
    controller_fd, follower_fd = os.openpty()
    tty.setraw(follower_fd)  # raw mode -- see run.py's comment on why
    try:
        machine = _build_echo_machine(controller_fd)
        os.write(follower_fd, b"A")
        run_interactive(machine, controller_fd, max_steps=1000)
        echoed = os.read(follower_fd, 1)
        assert echoed == b"A"
    finally:
        os.close(controller_fd)
        os.close(follower_fd)


def test_echo_rom_handles_multiple_bytes_in_order():
    controller_fd, follower_fd = os.openpty()
    tty.setraw(follower_fd)  # raw mode -- see run.py's comment on why
    try:
        machine = _build_echo_machine(controller_fd)
        os.write(follower_fd, b"hi")
        run_interactive(machine, controller_fd, max_steps=4000)
        echoed = os.read(follower_fd, 2)
        assert echoed == b"hi"
    finally:
        os.close(controller_fd)
        os.close(follower_fd)
