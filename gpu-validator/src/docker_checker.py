"""Docker and NVIDIA GPU container environment detection."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from typing import Any

from .models import CheckResult


class DockerChecker:
    """Check Docker, its daemon, NVIDIA runtime, and GPU containers."""

    _GPU_CONTAINER_IMAGE = "nvidia/cuda:12.4.1-base-ubuntu22.04"
    _COMMAND_TIMEOUT_SECONDS = 30
    _CONTAINER_TIMEOUT_SECONDS = 180

    def check(self) -> CheckResult:
        """Run the Docker environment and GPU container checks."""
        environment = self._check_environment()
        docker_ok, docker_detail = self._check_docker(environment)
        if not docker_ok:
            return CheckResult(
                check_name="docker",
                status="FAILED",
                message=docker_detail["message"],
                detail={"environment": environment, **docker_detail},
            )

        runtime_ok, runtime_detail = self._check_runtime(environment)
        if not runtime_ok:
            return CheckResult(
                check_name="docker",
                status="WARNING",
                message=(
                    "Docker is running, but GPU container test was skipped: "
                    f"{runtime_detail['message']}"
                ),
                detail={
                    "environment": environment,
                    **docker_detail,
                    "runtime": runtime_detail,
                },
            )

        container_ok, container_detail = self._check_gpu_container(
            environment["docker"]
        )
        if not container_ok:
            return CheckResult(
                check_name="docker",
                status="FAILED",
                message=container_detail["message"],
                detail={
                    "environment": environment,
                    **docker_detail,
                    "runtime": runtime_detail,
                    "container": container_detail,
                },
            )

        return CheckResult(
            check_name="docker",
            status="PASS",
            message="Docker GPU container validation passed",
            detail={
                "environment": environment,
                **docker_detail,
                "runtime": runtime_detail,
                "container": container_detail,
            },
        )

    @staticmethod
    def _check_environment() -> dict[str, str | None]:
        """Collect executable paths and PATH for environment diagnostics."""
        return {
            "python": sys.executable,
            "docker": shutil.which("docker"),
            "nvidia_container_cli": shutil.which("nvidia-container-cli"),
            "path": os.environ.get("PATH", ""),
        }

    def _check_docker(
        self, environment: dict[str, str | None]
    ) -> tuple[bool, dict[str, Any]]:
        """Check Docker installation and daemon availability."""
        docker_path = environment["docker"]
        if docker_path is None:
            return False, {"message": "docker command not found"}

        version_ok, version_message = self._run_command(
            [docker_path, "--version"], self._COMMAND_TIMEOUT_SECONDS
        )
        if not version_ok:
            return False, {"message": f"Docker is unavailable: {version_message}"}

        daemon_ok, daemon_message = self._run_command(
            [docker_path, "info"], self._COMMAND_TIMEOUT_SECONDS
        )
        if not daemon_ok:
            return False, {
                "docker_version": version_message,
                "message": f"Docker daemon is unavailable: {daemon_message}",
            }
        return True, {
            "docker_version": version_message,
            "daemon": "available",
        }

    def _check_runtime(
        self, environment: dict[str, str | None]
    ) -> tuple[bool, dict[str, str]]:
        """Check that NVIDIA Container Runtime tooling is available."""
        runtime_path = environment["nvidia_container_cli"]
        if runtime_path is None:
            return False, {"message": "nvidia-container-cli command not found"}

        runtime_ok, runtime_message = self._run_command(
            [runtime_path, "--version"], self._COMMAND_TIMEOUT_SECONDS
        )
        if not runtime_ok:
            return False, {"message": runtime_message}
        return True, {"version": runtime_message}

    def _check_gpu_container(self, docker_path: str | None) -> tuple[bool, dict[str, Any]]:
        """Run ``nvidia-smi`` inside a real CUDA GPU container."""
        if docker_path is None:
            return False, {"message": "docker command not found"}
        command = [
            docker_path,
            "run",
            "--rm",
            "--gpus",
            "all",
            self._GPU_CONTAINER_IMAGE,
            "nvidia-smi",
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=self._CONTAINER_TIMEOUT_SECONDS,
            )
        except FileNotFoundError:
            return False, {"message": "docker command not found"}
        except subprocess.TimeoutExpired:
            return False, {
                "message": (
                    "GPU container test timed out after "
                    f"{self._CONTAINER_TIMEOUT_SECONDS} seconds"
                )
            }
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "container command failed").strip()
            return False, {"message": f"GPU container test failed: {detail}"}
        except OSError as exc:
            return False, {"message": f"Unable to execute GPU container test: {exc}"}

        output = completed.stdout or completed.stderr
        parsed = self._parse_nvidia_smi(output)
        if parsed is None:
            return False, {
                "message": "GPU container ran, but nvidia-smi output was incomplete"
            }
        return True, parsed

    @staticmethod
    def _parse_nvidia_smi(output: str) -> dict[str, str] | None:
        """Extract clean GPU, driver, and CUDA values from ``nvidia-smi``."""
        gpu_match = re.search(
            r"\|\s*\d+\s+(?P<gpu>.+?)\s+(?:Off|On)\s+\|", output
        )
        driver_match = re.search(r"Driver Version:\s*([^\s|]+)", output)
        cuda_match = re.search(r"CUDA Version:\s*([^\s|]+)", output)
        if not (gpu_match and driver_match and cuda_match):
            return None
        return {
            "gpu": " ".join(gpu_match.group("gpu").split()),
            "driver": driver_match.group(1),
            "cuda": cuda_match.group(1),
        }

    @staticmethod
    def _run_command(command: list[str], timeout: int) -> tuple[bool, str]:
        """Run a command with a timeout and return readable output or error."""
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout,
            )
        except FileNotFoundError:
            return False, f"command not found: {command[0]}"
        except subprocess.TimeoutExpired:
            return False, f"command timed out after {timeout} seconds"
        except subprocess.CalledProcessError as exc:
            return False, (exc.stderr or exc.stdout or "command failed").strip()
        except OSError as exc:
            return False, f"unable to execute command: {exc}"

        output = (completed.stdout or completed.stderr).strip()
        return True, output or "command completed successfully"
