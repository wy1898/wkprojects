"""Collect CUDA toolkit and PyTorch availability without assuming either exists."""

from __future__ import annotations

from typing import Any
import sys

from .command_runner import CommandRunner


class RuntimeCollector:
    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    def collect(self) -> dict[str, Any]:
        nvcc = self.runner.run(["nvcc", "--version"])
        pytorch = self.runner.run([
            sys.executable,
            "-c",
            "import torch; print(f'torch={torch.__version__} cuda_available={torch.cuda.is_available()} cuda={torch.version.cuda} devices={torch.cuda.device_count()}')",
        ])
        return {"nvcc": nvcc.to_dict(), "pytorch": pytorch.to_dict()}
