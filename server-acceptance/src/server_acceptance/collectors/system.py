import json, platform, socket
from pathlib import Path
from ..models import Inventory
from ..services.runner import CommandRunner

class SystemCollector:
    def __init__(self, runner=None): self.runner = runner or CommandRunner()
    def _json(self, command):
        r = self.runner.run(command)
        return ({"status": r.status, "stdout": r.stdout, "stderr": r.stderr, "error": r.error}, r)
    def collect(self) -> Inventory:
        inv = Inventory()
        data, r = self._json(["lscpu", "-J"])
        if r.status == "AVAILABLE":
            vals = {x["field"].rstrip(":"): x["data"] for x in json.loads(r.stdout).get("lscpu", [])}
            inv.cpu = {"model": vals.get("Model name"), "sockets": _num(vals.get("Socket(s)")), "cores": _num(vals.get("Core(s) per socket")), "threads": _num(vals.get("CPU(s)")), "architecture": vals.get("Architecture")}
        else: inv.cpu = data
        data, r = self._json(["free", "-b"]); inv.memory = data if r.status != "AVAILABLE" else _free(r.stdout)
        data, r = self._json(["lsblk", "-J", "-o", "NAME,MODEL,SIZE,TYPE,TRAN"]); inv.storage = data if r.status != "AVAILABLE" else _storage(json.loads(r.stdout).get("blockdevices", []))
        data, r = self._json(["ip", "-j", "address"])
        inv.network = data if r.status != "AVAILABLE" else _network_inventory(json.loads(r.stdout), self.runner)
        data, r = self._json(["nvidia-smi", "--query-gpu=name,uuid,memory.total,pci.bus_id,driver_version", "--format=csv,noheader"]); inv.gpu = data if r.status != "AVAILABLE" else {"gpus": [dict(zip(["model","uuid","memory","pci_bus_id","driver"], [v.strip() for v in line.split(",")])) for line in r.stdout.splitlines()]}
        inv.os = {"hostname": socket.gethostname(), "os": platform.platform(), "kernel": platform.release(), "architecture": platform.machine()}
        inv.platform = {"manufacturer": None, "product_name": None, "bios": None, "status": "UNAVAILABLE", "message": "DMI collection is optional and may be unavailable in WSL/containers"}
        return inv

def _num(v):
    try: return int(v)
    except (TypeError, ValueError): return None
def _free(s):
    lines = s.splitlines(); row = next((x for x in lines if x.lower().startswith("mem")), "").split()
    return {"total_bytes": int(row[1]) if len(row)>1 else None, "available_bytes": int(row[6]) if len(row)>6 else None}

def _storage(devices):
    for item in devices:
        item["transport"] = item.get("tran") or "unknown"
        item["path"] = f"/dev/{item.get('name')}" if item.get("name") else None
        if item.get("children"): _storage(item["children"])
    return {"devices": devices, "status": "AVAILABLE"}

def classify_interface(interface: dict, sys_class_net: str = "/sys/class/net") -> str:
    name = interface.get("ifname", "")
    flags = set(interface.get("flags", []))
    if "LOOPBACK" in flags or name == "lo":
        return "loopback"
    path = Path(sys_class_net) / name
    if (path / "device").exists():
        return "physical"
    if (path / "bridge").exists() or (path / "tun_flags").exists():
        return "virtual/container"
    try:
        if (path / "iflink").read_text().strip() != (path / "ifindex").read_text().strip():
            return "virtual/container"
    except (OSError, ValueError):
        pass
    # WSL2 synthetic NICs may expose no PCI-backed /device symlink. The
    # kernel-reported Ethernet link type is still useful evidence here.
    if interface.get("link_type") == "ether":
        return "physical"
    return "unknown"

def _network_inventory(interfaces, runner=None):
    classified = [{**item, "classification": classify_interface(item)} for item in interfaces]
    if runner:
        for item in classified:
            if item["classification"] == "physical":
                speed = runner.run(["ethtool", item["ifname"]])
                item["speed_mbps"] = _speed(speed.stdout) if speed.status == "AVAILABLE" else None
                item["speed_status"] = speed.status
                driver = runner.run(["ethtool", "-i", item["ifname"]])
                item["driver"] = _driver(driver.stdout) if driver.status == "AVAILABLE" else None
    unknown = [item["ifname"] for item in classified if item["classification"] == "unknown"]
    return {"status": "UNAVAILABLE" if unknown else "AVAILABLE", "interfaces": classified,
            "physical_count": sum(item["classification"] == "physical" for item in classified),
            "unknown_interfaces": unknown,
            "message": f"Unable to classify interfaces: {', '.join(unknown)}" if unknown else None}

def _speed(text):
    for line in text.splitlines():
        if line.lower().strip().startswith("speed:"):
            value = line.split(":", 1)[1].strip().lower().replace("mb/s", "").strip()
            try: return int(float(value))
            except ValueError: return None
    return None
def _driver(text):
    for line in text.splitlines():
        if line.lower().startswith("driver:"): return line.split(":", 1)[1].strip()
    return None
