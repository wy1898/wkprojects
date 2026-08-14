from dataclasses import dataclass, field
from typing import Any

@dataclass
class Expectation:
    server: dict[str, Any] = field(default_factory=dict)
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Expectation":
        raw = dict(data.get("server", {}).get("expected", data.get("server", {})))
        for section in ("cpu", "memory", "storage", "raid", "network", "gpu", "os", "platform", "kubernetes"):
            if section in data:
                raw[section] = data[section]
        return cls(server={key: _normalize(value) for key, value in raw.items()})
    def to_dict(self) -> dict[str, Any]: return {"server": {"expected": self.server}}

def _normalize(value: Any) -> dict[str, Any] | Any:
    """Accept legacy integers as minimum requirements; prefer explicit rules."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return {"min": value, "legacy": True}
    if isinstance(value, dict) and ("min" in value or "minimum" in value or "exact" in value):
        if "minimum" in value and "min" not in value:
            value = {**value, "min": value["minimum"]}
        return value
    return value
