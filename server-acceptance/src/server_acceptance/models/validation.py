from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any

class Status(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"

@dataclass
class ValidationResult:
    component: str
    expected: Any
    actual: Any
    status: Status
    evidence: Any = None
    message: str = ""
    def to_dict(self):
        value = asdict(self); value["status"] = self.status.value; return value
