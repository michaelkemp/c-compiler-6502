"""Machine: CPU + Bus + ConsoleDevice wired together, with a step/run loop.

The "clock" stand-in described in docs/architecture.md -- run() just steps
the CPU up to a bounded number of times (no halt-detection convention
exists yet; that's a Phase 3/6 concern once we know what a program's
"done" trap looks like).
"""

from __future__ import annotations

from .bus import ROM_BASE, Bus
from .cpu import CPU, StepResult
from .trace import format_step


class Machine:
    def __init__(self, rom: bytes, rom_origin: int = ROM_BASE) -> None:
        self.bus = Bus()
        self.bus.load_rom(rom, origin=rom_origin)
        self.console = self.bus.console
        self.cpu = CPU(self.bus)
        self.cpu.reset()

    def step(self) -> StepResult:
        return self.cpu.step()

    def run(self, max_steps: int, trace: bool = False) -> list[StepResult]:
        results = []
        for _ in range(max_steps):
            result = self.step()
            if trace:
                print(format_step(result))
            results.append(result)
        return results
