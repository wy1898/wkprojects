"""NVIDIA GPU detection backed by the ``nvidia-smi`` command."""

from __future__ import annotations

import csv
import io
import subprocess

from .models import GPUInfo


class GPUChecker:
    """Inspect NVIDIA GPU information from the local host."""

    _QUERY_FIELDS = (
        "name",
        "memory.total",
        "driver_version",
        "temperature.gpu",
        "power.draw",
    )

    def check(self) -> GPUInfo:
        """Query and parse the first GPU reported by ``nvidia-smi``.

        Returns:
            Information collected from the real NVIDIA management utility.

        Raises:
            RuntimeError: If ``nvidia-smi`` is unavailable, fails, or returns
                output that cannot be parsed.
        """
        try:
            completed = subprocess.run(
                [
                    "nvidia-smi",
                    f"--query-gpu={','.join(self._QUERY_FIELDS)}",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("nvidia-smi was not found on PATH") from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "unknown error").strip()
            raise RuntimeError(f"nvidia-smi failed: {detail}") from exc
        except OSError as exc:
            raise RuntimeError(f"unable to execute nvidia-smi: {exc}") from exc

        cuda_version = self._query_cuda_version()
        return self._parse_output(completed.stdout, cuda_version)

    def _query_cuda_version(self) -> str:
        """Read the CUDA version reported by the NVIDIA driver."""
        try:
            completed = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                text=True,
                check=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("nvidia-smi was not found on PATH") from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "unknown error").strip()
            raise RuntimeError(f"nvidia-smi failed: {detail}") from exc
        except OSError as exc:
            raise RuntimeError(f"unable to execute nvidia-smi: {exc}") from exc

        marker = "CUDA Version:"
        for line in completed.stdout.splitlines():
            if marker in line:
                return line.split(marker, 1)[1].split("|", 1)[0].strip()
        return "N/A"

    def _parse_output(self, output: str, cuda_version: str) -> GPUInfo:
        """Parse one CSV row returned by ``nvidia-smi``."""
        rows = list(csv.reader(io.StringIO(output), skipinitialspace=True))
        if not rows or len(rows[0]) != len(self._QUERY_FIELDS):
            raise RuntimeError("nvidia-smi returned no parseable GPU information")

        row = [value.strip() for value in rows[0]]
        try:
            return GPUInfo(
                gpu_name=row[0],
                memory_total=float(row[1]),
                driver_version=row[2],
                cuda_version=cuda_version,
                temperature=float(row[3]),
                power_usage=float(row[4]),
            )
        except ValueError as exc:
            raise RuntimeError("nvidia-smi returned invalid GPU values") from exc
