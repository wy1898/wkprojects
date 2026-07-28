"""GPU information and environment checks.

The module deliberately keeps the CLI-facing API small: ``run_info`` and
``run_env`` are the two entry points used by :mod:`gpu_platform.cli`.
"""

from __future__ import annotations

import importlib.util
import csv
import os
import platform
import shutil
import subprocess
import sys
from typing import Any

from .output import print_env_table, print_error, print_gpu_table, print_header, print_info, print_success


_GPU_QUERY = (
    "index,name,driver_version,memory.total,memory.used,"
    "utilization.gpu,temperature.gpu"
)


def _nvidia_smi_path() -> str | None:
    """Return the available ``nvidia-smi`` executable, if any."""
    return shutil.which("nvidia-smi")


def _run_nvidia_smi(*arguments: str) -> tuple[str | None, str | None]:
    """Run ``nvidia-smi`` and return ``(stdout, error)``.

    Errors are converted into text so the commands remain useful on machines
    without an NVIDIA driver instead of raising a subprocess exception.
    """
    executable = _nvidia_smi_path()
    if executable is None:
        return None, "nvidia-smi was not found on PATH"

    try:
        result = subprocess.run(
            [executable, *arguments],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, str(exc)

    output = result.stdout.strip()
    if result.returncode != 0:
        error = result.stderr.strip() or output or f"exit code {result.returncode}"
        return None, error
    return output, None


def _format_gpu_info(output: str) -> list[str]:
    """Convert CSV output from ``nvidia-smi`` into readable lines."""
    lines: list[str] = []
    for fields in csv.reader(output.splitlines(), skipinitialspace=True):
        fields = [field.strip() for field in fields]
        if len(fields) != 7:
            continue
        index, name, driver, total, used, utilization, temperature = fields
        lines.append(
            f"GPU {index}: {name} | driver {driver} | memory {used}/{total} MiB "
            f"| utilization {utilization}% | temperature {temperature} C"
        )
    return lines


def _torch_status() -> dict[str, Any]:
    """Return optional PyTorch/CUDA status without making it a dependency."""
    if importlib.util.find_spec("torch") is None:
        return {"installed": False, "cuda_available": None, "version": None}

    try:
        import torch

        return {
            "installed": True,
            "cuda_available": bool(torch.cuda.is_available()),
            "version": getattr(torch, "__version__", "unknown"),
        }
    except Exception as exc:  # optional package failures must not break env
        return {
            "installed": True,
            "cuda_available": None,
            "version": None,
            "error": str(exc),
        }


def run_info() -> None:
    """Print detected NVIDIA GPU information."""
    print_header("GPU Platform Information")
    output, error = _run_nvidia_smi(
        f"--query-gpu={_GPU_QUERY}",
        "--format=csv,noheader,nounits",
    )

    if output:
        gpu_lines = _format_gpu_info(output)
        if gpu_lines:
            print_success("Status: available")
            for line in gpu_lines:
                print_gpu_table({"GPU": line})
            return

    print_error("Status: unavailable")
    print_info(error or "nvidia-smi returned no GPU information")


def run_env() -> None:
    """Print a diagnostic summary of the GPU software environment."""
    print_header("GPU Platform Environment")
    executable = _nvidia_smi_path()
    environment: dict[str, str] = {
        "Operating system": f"{platform.system()} {platform.release()}",
        "Python": f"{sys.version.split()[0]} ({sys.executable})",
        "nvidia-smi": (
            f"available ({executable})" if executable else "unavailable"
        ),
    }

    torch = _torch_status()
    if not torch["installed"]:
        environment["PyTorch"] = "not installed"
    elif torch.get("version"):
        environment["PyTorch"] = (
            f"{torch['version']} | CUDA available: "
            f"{'yes' if torch['cuda_available'] else 'no'}"
        )
    else:
        environment["PyTorch"] = f"installed but unavailable ({torch['error']})"

    cuda_environment = os.environ.get("CUDA_HOME") or os.environ.get("CUDA_PATH")
    environment["CUDA path"] = cuda_environment or "not set"
    print_env_table(environment)
