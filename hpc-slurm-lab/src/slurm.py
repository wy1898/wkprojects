"""Client interfaces for retrieving and managing Slurm jobs."""

import subprocess

try:
    from .models import Job, Node
except ImportError:  # pragma: no cover - supports direct script execution.
    from models import Job, Node


class SlurmError(RuntimeError):
    """Represent an error while communicating with Slurm."""


class SlurmClient:
    """Provide the application-facing interface to Slurm operations."""

    def __init__(self, use_mock: bool = False, timeout: float = 30.0) -> None:
        """Initialize the client with the selected data source.

        Args:
            use_mock: Whether Slurm queries should use mock data.
            timeout: Maximum duration in seconds for a real command.
        """
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        self.use_mock = use_mock
        self.timeout = timeout

    def get_jobs(self) -> str:
        """Return ``squeue`` output for the current data source."""
        if self.use_mock:
            return self._mock_jobs_output()
        return self._run_command(["squeue"])

    def get_nodes(self) -> str:
        """Return ``sinfo`` output for the current data source."""
        if self.use_mock:
            return self._mock_nodes_output()
        return self._run_command(["sinfo"])

    def submit_job(self, script_path: str) -> str:
        """Submit a job script and return the command output.

        Args:
            script_path: Path to the job script to submit.

        Returns:
            Output from the mock or real ``sbatch`` command.
        """
        if not script_path.strip():
            raise ValueError("script_path must not be empty")
        if self.use_mock:
            return "Submitted batch job 10001"
        return self._run_command(["sbatch", script_path])

    def cancel_job(self, job_id: int) -> str:
        """Cancel a job and return the command output.

        Args:
            job_id: ID of the job to cancel.

        Returns:
            Output from the mock or real ``scancel`` command.
        """
        if job_id <= 0:
            raise ValueError("job_id must be greater than zero")
        if self.use_mock:
            return f"Job {job_id} cancelled"
        return self._run_command(["scancel", str(job_id)])

    def get_job_history(self) -> str:
        """Return ``sacct`` output for the current data source."""
        if self.use_mock:
            return self._mock_job_history_output()
        return self._run_command(["sacct"])

    def _run_command(self, command: list[str]) -> str:
        """Run a Slurm command without invoking a shell.

        Args:
            command: Executable and arguments to run.

        Returns:
            Captured standard output.

        Raises:
            SlurmError: If the executable is missing, fails, or times out.
        """
        if not command or any(not part for part in command):
            raise ValueError("command must contain a non-empty executable")
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                check=True,
                text=True,
                timeout=self.timeout,
            )
        except FileNotFoundError as error:
            raise SlurmError(f"command not found: {command[0]}") from error
        except subprocess.TimeoutExpired as error:
            raise SlurmError(
                f"command timed out after {self.timeout:g} seconds"
            ) from error
        except subprocess.CalledProcessError as error:
            message = (error.stderr or error.stdout or "command failed").strip()
            raise SlurmError(message) from error
        return result.stdout

    def _mock_jobs_output(self) -> str:
        """Return mock ``squeue`` output used by the MVP."""
        return (
            "JOBID NAME STATE USER PARTITION NODE\n"
            "1001 analysis RUNNING alice compute node01\n"
            "1002 training PENDING bob gpu node02\n"
        )

    def _mock_nodes_output(self) -> str:
        """Return mock ``sinfo`` output used by the MVP."""
        return (
            "NODE STATE GPU_COUNT CPU_COUNT\n"
            "node01 IDLE 0 64\n"
            "node02 ALLOCATED 4 128\n"
        )

    def _mock_job_history_output(self) -> str:
        """Return mock ``sacct`` output used by the MVP."""
        return (
            "JOBID NAME STATE USER PARTITION NODE\n"
            "9001 completed COMPLETED alice compute node01\n"
            "9002 failed FAILED bob gpu node02\n"
        )
