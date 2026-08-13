"""Structured diagnostic conclusions produced by analyzers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(slots=True)
class Evidence:
    """A concrete piece of collected data supporting a finding."""

    source: str
    matched: str
    detail: str = ""


@dataclass(slots=True)
class Finding:
    error_id: str
    severity: Severity
    title: str
    description: str
    evidence: list[Evidence] = field(default_factory=list)
    possible_causes: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        data["evidence"] = [asdict(item) for item in self.evidence]
        return data
