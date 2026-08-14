from ..models import Status, ValidationResult

class ValidationEngine:
    def validate(self, inventory, expectation):
        actual = inventory.to_dict(); rules = expectation.server; out = []
        checks = [
            ("CPU", "cpu_sockets", actual["cpu"].get("sockets"), rules.get("cpu_sockets")),
            ("Memory", "memory_gb", _memory(actual["memory"]), rules.get("memory_gb")),
            ("Storage", "storage_count", _storage_count(actual["storage"]), rules.get("storage_count")),
            ("Network", "network_interfaces", actual["network"].get("physical_count") if isinstance(actual["network"], dict) else None, rules.get("network_interfaces")),
            ("GPU", "gpu_count", _gpu_count(actual["gpu"]), rules.get("gpu_count")),
        ]
        for component, name, value, rule in checks:
            if rule is not None: out.append(_result(component, name, rule, value, actual.get(component.lower(), {})))
        out.extend(self._extended(actual, rules))
        raid = actual.get("raid", {})
        if rules.get("raid") is not None:
            out.append(_result("RAID", "raid.status", rules["raid"], raid.get("state"), raid))
        elif raid.get("status") == "UNAVAILABLE":
            out.append(ValidationResult("RAID", "optional capability", None, Status.UNAVAILABLE, raid, "RAID capability could not be determined."))
        health = actual.get("storage", {}).get("health") if isinstance(actual.get("storage"), dict) else None
        if health and health.get("status") == "UNAVAILABLE":
            out.append(ValidationResult("Storage", "optional SMART/NVMe health", None, Status.UNAVAILABLE, health, "Storage health could not be determined."))
        k8s = rules.get("kubernetes")
        if k8s:
            actual_k8s = actual.get("k8s", {})
            for key in ("container_runtime", "kubelet", "kubectl"):
                if k8s.get(key) != "optional":
                    item = actual_k8s.get(key, {})
                    out.append(ValidationResult("Kubernetes", f"{key} availability", k8s.get(key), item.get("status"), actual_k8s, "Kubernetes node capability is unavailable." if item.get("status") != "AVAILABLE" else "Kubernetes node capability is available."))
                elif actual_k8s.get(key, {}).get("status") != "AVAILABLE":
                    out.append(ValidationResult("Kubernetes", f"optional {key}", "optional", Status.UNAVAILABLE, actual_k8s.get(key, {}), f"{key} is not installed or accessible."))
        return out

    def _extended(self, actual, rules):
        out = []
        storage = rules.get("storage", {})
        devices = _storage_devices(actual["storage"])
        if storage.get("count") is not None: out.append(_result("Storage", "storage.count", storage["count"], len(devices), actual["storage"]))
        if storage.get("type") is not None:
            rule = storage["type"]; values = [str(x.get("transport", x.get("tran", "unknown"))).lower() for x in devices]
            out.append(_result("Storage", "storage.type", rule, values, actual["storage"], lambda r,v: all(_match(r,x) for x in v)))
        if storage.get("min_capacity_gb") is not None:
            capacity = sum(_size_gb(x.get("size")) for x in devices)
            out.append(_result("Storage", "storage.min_capacity_gb", {"min": storage["min_capacity_gb"]}, capacity, actual["storage"]))
        network = rules.get("network", {})
        if network.get("physical_count") is not None: out.append(_result("Network", "network.physical_count", network["physical_count"], actual["network"].get("physical_count") if isinstance(actual["network"], dict) else None, actual["network"]))
        if network.get("min_speed_mbps") is not None:
            speeds = [x.get("speed_mbps") for x in actual["network"].get("interfaces", []) if x.get("classification") == "physical"]
            value = min(speeds) if speeds and all(x is not None for x in speeds) else None
            out.append(_result("Network", "network.min_speed_mbps", {"min": network["min_speed_mbps"]}, value, actual["network"], message="Link speed could not be determined."))
        gpu = rules.get("gpu", {})
        gpus = actual["gpu"].get("gpus", []) if isinstance(actual["gpu"], dict) else []
        if gpu.get("count") is not None: out.append(_result("GPU", "gpu.count", gpu["count"], len(gpus), actual["gpu"]))
        if gpu.get("model") is not None:
            rule = gpu["model"]; value = [x.get("model") for x in gpus]; out.append(_result("GPU", "gpu.model", rule, value, actual["gpu"], lambda r,v: all(_match(r,x) for x in v)))
        if gpu.get("min_memory_gb") is not None:
            values = [_size_gb(x.get("memory")) for x in gpus]; out.append(_result("GPU", "gpu.min_memory_gb", {"min": gpu["min_memory_gb"]}, min(values) if values else None, actual["gpu"]))
        cpu = rules.get("cpu", {})
        if cpu.get("sockets") is not None: out.append(_result("CPU", "cpu.sockets", cpu["sockets"], actual["cpu"].get("sockets"), actual["cpu"]))
        if cpu.get("min_cores") is not None: out.append(_result("CPU", "cpu.min_cores", {"min": cpu["min_cores"]}, actual["cpu"].get("cores"), actual["cpu"]))
        memory = rules.get("memory", {})
        if memory.get("min_gb") is not None: out.append(_result("Memory", "memory.min_gb", {"min": memory["min_gb"]}, _memory(actual["memory"]), actual["memory"]))
        if memory.get("exact_gb") is not None: out.append(_result("Memory", "memory.exact_gb", {"exact": memory["exact_gb"]}, _memory(actual["memory"]), actual["memory"]))
        os_rules = rules.get("os", {})
        for key, value in (("distribution", actual["os"].get("distribution") or actual["os"].get("os")), ("architecture", actual["os"].get("architecture"))):
            if key in os_rules: out.append(_result("OS", f"os.{key}", os_rules[key], value, actual["os"]))
        return out

def _result(component, name, rule, actual, evidence, comparator=None, message=None):
    if actual is None: return ValidationResult(component, rule, actual, Status.UNAVAILABLE, evidence, message or f"{name} could not be collected")
    passed = comparator(rule, actual) if comparator else _compare(rule, actual)
    if passed: return ValidationResult(component, rule, actual, Status.PASS, evidence, f"Detected {actual}; expectation satisfied")
    return ValidationResult(component, rule, actual, Status.FAIL, evidence, message or f"Expected {rule}, detected {actual}")
def _compare(rule, actual):
    if isinstance(rule, dict):
        if "exact" in rule: return actual == rule["exact"]
        return actual >= rule.get("min", rule.get("minimum"))
    return actual >= rule
def _match(rule, value):
    if isinstance(rule, dict): rule = rule.get("exact", rule.get("min"))
    return str(value).lower() == str(rule).lower()
def _memory(v): return round((v.get("total_bytes") or 0) / 1024**3, 2) if isinstance(v, dict) and "total_bytes" in v else None
def _storage_devices(v): return v if isinstance(v, list) else v.get("devices", []) if isinstance(v, dict) else []
def _storage_count(v): return len([x for x in _storage_devices(v) if x.get("type") == "disk"])
def _gpu_count(v): return len(v.get("gpus", [])) if isinstance(v, dict) and "gpus" in v else None
def _size_gb(value):
    try:
        text = str(value).upper().replace(" ", "")
        units = (("TIB", 1024), ("TB", 1024), ("GIB", 1), ("GB", 1), ("MIB", 1 / 1024), ("MB", 1 / 1024), ("T", 1024), ("G", 1), ("M", 1 / 1024))
        for suffix, factor in units:
            if text.endswith(suffix): return float(text[:-len(suffix)]) * factor
        return float(text) / (1024 ** 3)
    except (TypeError, ValueError): return 0
