import json
from ..services.runner import CommandRunner

class StorageHealthCollector:
    """Collect optional SMART/NVMe health; inability to inspect is not disk failure."""
    def __init__(self, runner=None): self.runner = runner or CommandRunner()
    def collect(self, devices):
        results = []
        for device in devices:
            name = device.get("path") or f"/dev/{device.get('name')}"
            if not device.get("name"): continue
            command = ["nvme", "smart-log", name] if str(device.get("transport", "")).lower() == "nvme" else ["smartctl", "-H", "-A", name]
            result = self.runner.run(command)
            results.append({"device": name, "status": "UNAVAILABLE" if result.status == "UNAVAILABLE" else ("AVAILABLE" if result.return_code == 0 else "UNAVAILABLE"), "stdout": result.stdout, "stderr": result.stderr, "error": result.error})
        return {"devices": results, "status": "AVAILABLE" if results and any(x["status"] == "AVAILABLE" for x in results) else "UNAVAILABLE"}
