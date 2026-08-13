"""Collect NVIDIA driver facts through nvidia-smi."""

from __future__ import annotations

from typing import Any

from .command_runner import CommandRunner


class GPUCollector:
    QUERY_FIELDS = "name,uuid,pci.bus_id,driver_version,persistence_mode,memory.total,memory.used,temperature.gpu,ecc.errors.uncorrected.volatile.total"

    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    def collect(self) -> dict[str, Any]:
        summary = self.runner.run(["nvidia-smi"])
        query = self.runner.run([
            "nvidia-smi", f"--query-gpu={self.QUERY_FIELDS}", "--format=csv,noheader,nounits"
        ])
        gpus: list[dict[str, str]] = []
        if query.succeeded:
            keys = ["name", "uuid", "pci_bus_id", "driver_version", "persistence_mode", "memory_total_mib", "memory_used_mib", "temperature_c", "ecc_uncorrected"]
            for line in query.stdout.splitlines():
                values = [value.strip() for value in line.split(",")]
                if len(values) == len(keys):
                    gpus.append(dict(zip(keys, values)))
        return {"nvidia_smi": summary.to_dict(), "query": query.to_dict(), "gpu_count": len(gpus), "gpus": gpus}
