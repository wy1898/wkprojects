"""Command-line entry point for the Slurm Job Management Tool."""

import argparse
import sys

try:
    from .formatter import SlurmFormatter
    from .parser import ParserError, SlurmParser
    from .slurm import SlurmClient, SlurmError
except ImportError:  # pragma: no cover - supports direct script execution.
    from formatter import SlurmFormatter
    from parser import ParserError, SlurmParser
    from slurm import SlurmClient, SlurmError


def _positive_integer(value: str) -> int:
    """Parse a positive integer command-line argument."""
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Manage and inspect Slurm jobs.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("jobs", help="List current jobs.")
    commands.add_parser("nodes", help="List compute nodes.")

    submit_parser = commands.add_parser("submit", help="Submit a job script.")
    submit_parser.add_argument("script_path", help="Path to the job script.")

    cancel_parser = commands.add_parser("cancel", help="Cancel a job.")
    cancel_parser.add_argument("job_id", type=_positive_integer, help="Job ID.")
    commands.add_parser("history", help="List historical jobs.")
    return parser


def main(argv: list[str] | None = None) -> None:
    """Run the command-line interface for the supplied arguments."""
    parser = build_parser()
    args = parser.parse_args(argv)
    client = SlurmClient()
    slurm_parser = SlurmParser()
    formatter = SlurmFormatter()

    try:
        if args.command == "jobs":
            jobs = slurm_parser.parse_jobs(client.get_jobs())
            print(formatter.format_jobs(jobs))
        elif args.command == "nodes":
            nodes = slurm_parser.parse_nodes(client.get_nodes())
            print(formatter.format_nodes(nodes))
        elif args.command == "submit":
            raw_output = client.submit_job(args.script_path)
            job_id = slurm_parser.parse_submission(raw_output)
            print(formatter.format_submission(job_id))
        elif args.command == "cancel":
            raw_output = client.cancel_job(args.job_id)
            job_id = slurm_parser.parse_cancellation(raw_output)
            print(formatter.format_cancellation(job_id))
        elif args.command == "history":
            jobs = slurm_parser.parse_job_history(client.get_job_history())
            print(formatter.format_history(jobs))
    except (ParserError, SlurmError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
