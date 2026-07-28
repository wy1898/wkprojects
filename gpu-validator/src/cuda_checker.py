"""CUDA Toolkit detection backed by ``nvcc``."""

from __future__ import annotations

import platform
import re
import subprocess

from .models import CheckResult


class CUDAChecker:
    """Inspect the locally installed CUDA Toolkit and Python runtime."""

    def check(self) -> CheckResult:
        """Run ``nvcc --version`` and report the detected versions.

        Returns:
            A result describing whether CUDA Toolkit information was detected.
        """
        python_version = platform.python_version()
        try:
            completed = subprocess.run(
                ["nvcc", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError:
            return CheckResult(
                check_name="cuda",
                status="failed",
                message=f"nvcc was not found on PATH; Python {python_version}",
            )
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "unknown error").strip()
            return CheckResult(
                check_name="cuda",
                status="failed",
                message=f"nvcc failed: {detail}; Python {python_version}",
            )
        except OSError as exc:
            return CheckResult(
                check_name="cuda",
                status="failed",
                message=f"Unable to execute nvcc: {exc}; Python {python_version}",
            )

        match = re.search(r"release\s+([0-9]+(?:\.[0-9]+)+)", completed.stdout)
        if match is None:
            return CheckResult(
                check_name="cuda",
                status="failed",
                message=f"Could not parse CUDA Toolkit version; Python {python_version}",
            )

        return CheckResult(
            check_name="cuda",
            status="passed",
            message=f"CUDA Toolkit {match.group(1)} detected; Python {python_version}",
        )
