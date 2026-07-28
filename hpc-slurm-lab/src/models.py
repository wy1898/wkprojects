"""Data models used by the Slurm Job Management Tool."""

from dataclasses import dataclass


@dataclass
class Job:
    """Represent a Slurm job."""

    job_id: int
    name: str
    state: str
    user: str
    partition: str
    node: str


@dataclass
class Node:
    """Represent a Slurm compute node."""

    node_name: str
    state: str
    gpu_count: int
    cpu_count: int
