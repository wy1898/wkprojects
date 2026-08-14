from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass
class Inventory:
    cpu: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    storage: dict[str, Any] = field(default_factory=dict)
    raid: dict[str, Any] = field(default_factory=dict)
    network: dict[str, Any] = field(default_factory=dict)
    gpu: dict[str, Any] = field(default_factory=dict)
    os: dict[str, Any] = field(default_factory=dict)
    platform: dict[str, Any] = field(default_factory=dict)
    k8s: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)
