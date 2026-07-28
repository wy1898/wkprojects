"""Parse Slurm command output into application data models."""

import re

try:
    from .models import Job, Node
except ImportError:  # pragma: no cover - supports direct script execution.
    from models import Job, Node


class ParserError(ValueError):
    """Represent invalid or incomplete Slurm command output."""


class SlurmParser:
    """Convert supported Slurm output into data models and identifiers."""

    def parse_jobs(self, raw_output: str) -> list[Job]:
        """Parse job output into :class:`Job` objects.

        Args:
            raw_output: Job output with a header followed by data rows.

        Returns:
            Jobs represented by the supplied output.

        Raises:
            ParserError: If the output is empty or contains invalid rows.
        """
        rows = self._parse_rows(raw_output, 6, "job")
        return [
            Job(
                job_id=self._parse_integer(fields[0], "job ID"),
                name=fields[1],
                state=fields[2],
                user=fields[3],
                partition=fields[4],
                node=fields[5],
            )
            for fields in rows
        ]

    def parse_nodes(self, raw_output: str) -> list[Node]:
        """Parse node output into :class:`Node` objects.

        Args:
            raw_output: Node output with a header followed by data rows.

        Returns:
            Nodes represented by the supplied output.

        Raises:
            ParserError: If the output is empty or contains invalid rows.
        """
        rows = self._parse_rows(raw_output, 4, "node")
        return [
            Node(
                node_name=fields[0],
                state=fields[1],
                gpu_count=self._parse_integer(fields[2], "GPU count"),
                cpu_count=self._parse_integer(fields[3], "CPU count"),
            )
            for fields in rows
        ]

    def parse_job_history(self, raw_output: str) -> list[Job]:
        """Parse historical job output into :class:`Job` objects."""
        return self.parse_jobs(raw_output)

    def parse_submission(self, raw_output: str) -> int:
        """Extract the submitted job ID from ``sbatch`` output.

        Raises:
            ParserError: If no job ID is present in the output.
        """
        match = re.search(r"Submitted batch job\s+(\d+)", raw_output)
        if match is None:
            raise ParserError("unable to parse submitted job ID")
        return int(match.group(1))

    def parse_cancellation(self, raw_output: str) -> int:
        """Extract the cancelled job ID from ``scancel`` output.

        Raises:
            ParserError: If no job ID is present in the output.
        """
        match = re.search(r"Job\s+(\d+)\s+cancelled", raw_output)
        if match is None:
            raise ParserError("unable to parse cancelled job ID")
        return int(match.group(1))

    @staticmethod
    def _parse_rows(
        raw_output: str,
        field_count: int,
        record_name: str,
    ) -> list[list[str]]:
        """Return validated data rows after removing the output header."""
        lines = [line.split() for line in raw_output.splitlines() if line.strip()]
        if not lines:
            raise ParserError(f"empty {record_name} output")
        rows = lines[1:]
        for row in rows:
            if len(row) < field_count:
                raise ParserError(f"invalid {record_name} row")
        return rows

    @staticmethod
    def _parse_integer(value: str, field_name: str) -> int:
        """Convert a field to an integer with a parser-specific error."""
        try:
            return int(value)
        except ValueError as error:
            raise ParserError(f"invalid {field_name}: {value}") from error
