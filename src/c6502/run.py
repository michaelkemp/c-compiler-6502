"""A small CLI: load a ROM image, attach its ACIA to a real pseudo-
terminal, and run it -- so a real terminal program (screen, minicom,
PuTTY) can connect to a running Machine the way it would connect to real
hardware over a serial cable. See docs/architecture.md's Console I/O
device section and docs/roadmap.md's Phase 2 follow-up.
"""

from __future__ import annotations

import argparse
import os
import select
import sys
import tty
from typing import List, Optional

from .emulator.cpu import StepResult
from .emulator.machine import Machine
from .emulator.trace import format_step


def run_interactive(
    machine: Machine,
    controller_fd: int,
    trace: bool = False,
    max_steps: Optional[int] = None,
) -> List[StepResult]:
    """Pump bytes between a pty and the machine's ACIA, stepping it.

    Non-blocking-polls controller_fd for input each iteration rather than
    ever blocking on it -- matching real hardware, where the CPU is free
    to keep running (or just keep polling RDRF) whether or not a byte has
    arrived yet, rather than the process itself stalling.
    """
    results: List[StepResult] = []
    steps_done = 0
    while max_steps is None or steps_done < max_steps:
        readable, _, _ = select.select([controller_fd], [], [], 0)
        if readable:
            data = os.read(controller_fd, 4096)
            if data:
                machine.acia.feed_input(data)

        result = machine.step()
        if trace:
            print(format_step(result), file=sys.stderr)
        results.append(result)
        steps_done += 1
    return results


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run a 6502 ROM image with live serial I/O over a pty."
    )
    parser.add_argument("rom", help="path to a raw binary ROM image")
    parser.add_argument(
        "--origin",
        type=lambda s: int(s, 0),
        default=0x8000,
        help="load address for the ROM image (default 0x8000)",
    )
    parser.add_argument(
        "--trace", action="store_true", help="print each executed instruction to stderr"
    )
    args = parser.parse_args(argv)

    with open(args.rom, "rb") as f:
        rom_data = f.read()

    controller_fd, follower_fd = os.openpty()
    # Put the pty in raw mode: by default it's canonical/line-buffered,
    # so bytes we transmit (master write -> slave read) would sit stuck
    # in the line discipline's buffer instead of reaching the connected
    # terminal immediately. A real serial link is 8-bit clean with no
    # such buffering, so raw mode is what actually matches "a real
    # terminal attached over a serial cable."
    tty.setraw(follower_fd)
    machine = Machine(
        rom_data,
        rom_origin=args.origin,
        on_transmit=lambda byte: os.write(controller_fd, bytes([byte])),
    )
    follower_path = os.ttyname(follower_fd)
    print(f"Listening on {follower_path}", file=sys.stderr)
    print(f"Connect with: screen {follower_path} 9600", file=sys.stderr)
    print("Press Ctrl+C here to stop the emulator.", file=sys.stderr)

    try:
        run_interactive(machine, controller_fd, trace=args.trace)
    except KeyboardInterrupt:
        pass
    finally:
        os.close(controller_fd)
        os.close(follower_fd)


if __name__ == "__main__":
    main()
