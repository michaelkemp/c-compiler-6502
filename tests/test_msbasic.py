"""Validates that real, unmodified Microsoft BASIC boots and runs a
program against our AciaDevice -- see docs/roadmap.md's "run real
Microsoft BASIC" follow-up. Not vendored (see scripts/fetch_msbasic.sh);
run scripts/fetch_msbasic.sh && scripts/build_msbasic.sh once to build
msbasic/build/msbasic.bin before this test can run.
"""

import os

import pytest

from c6502.emulator.machine import Machine

ROM_PATH = os.path.join(os.path.dirname(__file__), "..", "msbasic", "build", "msbasic.bin")
MAX_STEPS = 5_000_000  # observed ~3M to boot + run one line; headroom for slop


@pytest.mark.slow
def test_basic_boots_and_runs_a_line():
    if not os.path.exists(ROM_PATH):
        pytest.skip(
            "msbasic/build/msbasic.bin not found -- run scripts/fetch_msbasic.sh "
            "and scripts/build_msbasic.sh to build it."
        )

    with open(ROM_PATH, "rb") as f:
        rom = f.read()

    out = bytearray()
    machine = Machine(rom, rom_origin=0x8000, on_transmit=out.append)

    # Accept the defaults for both setup prompts (MEMORY SIZE?, TERMINAL
    # WIDTH?), then run a line of BASIC.
    machine.acia.feed_input(b"\r\rPRINT 1+1\r")

    for _ in range(MAX_STEPS):
        machine.step()

    text = out.decode("ascii", errors="replace")
    assert "COPYRIGHT 1977 BY MICROSOFT CO." in text
    assert "PRINT 1+1" in text
    assert " 2 " in text
    assert text.count("OK") >= 2  # one ready prompt before, one after
