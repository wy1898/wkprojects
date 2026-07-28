"""Orchestration for the complete GPU environment validation workflow."""

from __future__ import annotations

from dataclasses import asdict
from typing import Callable

from .benchmark import BenchmarkRunner
from .cuda_checker import CUDAChecker
from .docker_checker import DockerChecker
from .gpu_checker import GPUChecker
from .models import CheckResult, GPUInfo, ValidationReport
from .torch_checker import TorchChecker


class ValidationRunner:
    """Run GPU, CUDA, PyTorch, and benchmark checks in order."""

    def __init__(self) -> None:
        """Initialize the validation components."""
        self.gpu_checker = GPUChecker()
        self.cuda_checker = CUDAChecker()
        self.torch_checker = TorchChecker()
        self.docker_checker = DockerChecker()
        self.benchmark_runner = BenchmarkRunner()

    def run(self) -> ValidationReport:
        """Execute the complete validation sequence.

        Returns:
            An aggregate report containing every check and the final result.
        """
        checks: list[CheckResult] = []
        gpu_result = self._run_gpu_check()
        checks.append(self._gpu_to_check_result(gpu_result))

        cuda_result = self._run_check("cuda", self.cuda_checker.check)
        checks.append(self._normalize_check_result(cuda_result))

        torch_result = self._run_check("pytorch", self.torch_checker.check)
        checks.append(self._normalize_check_result(torch_result))

        checks.append(self._run_docker_check())

        benchmark_result = self._run_check("benchmark", self.benchmark_runner.run)
        checks.append(self._normalize_check_result(benchmark_result))

        return ValidationReport(checks=checks, final_result=self._final_result(checks))

    def _run_docker_check(self) -> CheckResult:
        """Add the Docker flow node without implementing Docker detection."""
        try:
            result = self.docker_checker.check()
        except Exception as exc:
            return CheckResult(
                check_name="docker",
                status="FAILED",
                message=f"docker check failed: {exc}",
            )
        if result is None:
            return CheckResult(
                check_name="docker",
                status="SKIPPED",
                message="Docker check is not implemented in this phase",
            )
        return self._normalize_check_result(result)

    def _run_gpu_check(self) -> GPUInfo | CheckResult:
        """Run GPU detection and convert execution errors to a result."""
        try:
            return self.gpu_checker.check()
        except Exception as exc:
            return CheckResult(
                check_name="gpu",
                status="FAILED",
                message=f"GPU check failed: {exc}",
            )

    @staticmethod
    def _run_check(name: str, check: Callable[[], CheckResult]) -> CheckResult:
        """Run a checker callable and normalize unexpected exceptions."""
        try:
            return check()
        except Exception as exc:
            return CheckResult(
                check_name=name,
                status="FAILED",
                message=f"{name} check failed: {exc}",
            )

    @staticmethod
    def _gpu_to_check_result(result: GPUInfo | CheckResult) -> CheckResult:
        """Convert a GPU result into the common check result model."""
        if isinstance(result, GPUInfo):
            return CheckResult(
                check_name="gpu",
                status="PASS",
                message="GPU detected",
                detail=asdict(result),
            )
        return ValidationRunner._normalize_check_result(result)

    @staticmethod
    def _normalize_check_result(result: CheckResult) -> CheckResult:
        """Normalize checker status values without changing their meaning."""
        status = result.status.upper()
        if status == "PASSED":
            status = "PASS"
        return CheckResult(
            check_name=result.check_name,
            status=status,
            message=result.message,
            detail=result.detail,
        )

    @staticmethod
    def _final_result(checks: list[CheckResult]) -> CheckResult:
        """Derive PASS, WARNING, or FAILED from critical check outcomes."""
        critical_names = {"gpu", "pytorch", "benchmark"}
        critical_failures = [
            check.check_name
            for check in checks
            if check.check_name in critical_names and check.status == "FAILED"
        ]
        warnings = [
            check.check_name
            for check in checks
            if (
                check.check_name not in critical_names
                and check.status in {"FAILED", "SKIPPED"}
            )
            or (check.check_name == "benchmark" and check.status == "SKIPPED")
        ]

        if critical_failures:
            return CheckResult(
                check_name="final_result",
                status="FAILED",
                message=(
                    "Core validation failed: " + ", ".join(critical_failures)
                ),
                detail={"failed_checks": critical_failures},
            )
        if warnings:
            return CheckResult(
                check_name="final_result",
                status="WARNING",
                message=("Core validation passed; non-critical checks need attention: "
                         + ", ".join(warnings)),
                detail={"warning_checks": warnings},
            )
        return CheckResult(
            check_name="final_result",
            status="PASS",
            message="All validation checks passed",
        )
