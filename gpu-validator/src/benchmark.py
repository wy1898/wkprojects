"""Real GPU matrix multiplication benchmark implementation."""

from __future__ import annotations

import time

from .models import CheckResult


class BenchmarkRunner:
    """Run a small matrix multiplication workload on an NVIDIA GPU."""

    def __init__(self, matrix_size: int = 1024) -> None:
        """Create a benchmark runner.

        Args:
            matrix_size: Width and height of each square matrix.
        """
        if matrix_size <= 0:
            raise ValueError("matrix_size must be positive")
        self.matrix_size = matrix_size

    def run(self) -> CheckResult:
        """Execute GPU matrix multiplication and measure elapsed time.

        Returns:
            ``CheckResult`` with ``PASSED``, ``SKIPPED``, or ``FAILED`` status.
        """
        try:
            import torch
        except ImportError as exc:
            return CheckResult(
                check_name="benchmark",
                status="SKIPPED",
                message=f"PyTorch is not installed: {exc}",
            )

        try:
            if not torch.cuda.is_available():
                return CheckResult(
                    check_name="benchmark",
                    status="SKIPPED",
                    message="CUDA is not available; GPU benchmark skipped",
                )

            device = torch.device("cuda")
            left = torch.rand(
                (self.matrix_size, self.matrix_size), device=device
            )
            right = torch.rand(
                (self.matrix_size, self.matrix_size), device=device
            )
            torch.cuda.synchronize(device)
            start = time.perf_counter()
            torch.matmul(left, right)
            torch.cuda.synchronize(device)
            elapsed_ms = (time.perf_counter() - start) * 1000
        except Exception as exc:
            return CheckResult(
                check_name="benchmark",
                status="FAILED",
                message=f"GPU benchmark failed: {exc}",
            )

        return CheckResult(
            check_name="benchmark",
            status="PASSED",
            message=(
                f"{self.matrix_size}x{self.matrix_size} torch.matmul completed "
                f"in {elapsed_ms:.3f} ms"
            ),
        )
