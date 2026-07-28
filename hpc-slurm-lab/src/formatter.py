"""Format Slurm data models for terminal display."""

try:
    from .models import Job, Node
except ImportError:  # pragma: no cover - supports direct script execution.
    from models import Job, Node


class SlurmFormatter:
    """Convert Slurm data models and results into terminal text."""

    def format_jobs(self, jobs: list[Job]) -> str:
        """Format jobs as a plain-text table."""
        rows = [
            [
                str(job.job_id),
                job.name,
                job.state,
                job.user,
                job.partition,
                job.node,
            ]
            for job in jobs
        ]
        return self._format_table(
            ["JOBID", "NAME", "STATE", "USER", "PARTITION", "NODE"],
            rows,
        )

    def format_nodes(self, nodes: list[Node]) -> str:
        """Format nodes as a plain-text table."""
        rows = [
            [
                node.node_name,
                node.state,
                str(node.gpu_count),
                str(node.cpu_count),
            ]
            for node in nodes
        ]
        return self._format_table(
            ["NODE", "STATE", "GPU_COUNT", "CPU_COUNT"],
            rows,
        )

    def format_history(self, jobs: list[Job]) -> str:
        """Format historical jobs as a plain-text table."""
        return self.format_jobs(jobs)

    def format_submission(self, job_id: int) -> str:
        """Format a successful job submission message."""
        return f"Job submitted successfully.\nJob ID: {job_id}"

    def format_cancellation(self, job_id: int) -> str:
        """Format a successful job cancellation message."""
        return f"Job {job_id} cancelled successfully."

    @staticmethod
    def _format_table(headers: list[str], rows: list[list[str]]) -> str:
        """Render headers and rows as a simple aligned text table."""
        widths = [
            max([len(headers[index])] + [len(row[index]) for row in rows])
            for index in range(len(headers))
        ]
        header = " | ".join(
            headers[index].ljust(widths[index]) for index in range(len(headers))
        )
        separator = "-+-".join("-" * width for width in widths)
        body = [
            " | ".join(row[index].ljust(widths[index]) for index in range(len(row)))
            for row in rows
        ]
        return "\n".join([header, separator, *body])
