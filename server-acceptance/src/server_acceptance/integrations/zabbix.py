def build_template(inventory, name="server-acceptance"):
    """Build a Zabbix-compatible mapping export; no Zabbix server is contacted."""
    items = [
        {"key": "server.cpu.sockets", "name": "CPU socket count", "value": inventory.get("cpu", {}).get("sockets")},
        {"key": "server.cpu.cores", "name": "CPU core count", "value": inventory.get("cpu", {}).get("cores")},
        {"key": "server.memory.total_bytes", "name": "Memory total bytes", "value": inventory.get("memory", {}).get("total_bytes")},
        {"key": "server.gpu.count", "name": "GPU count", "value": len(inventory.get("gpu", {}).get("gpus", []))},
        {"key": "server.storage.count", "name": "Storage device count", "value": len(inventory.get("storage", {}).get("devices", [])) if isinstance(inventory.get("storage"), dict) else 0},
        {"key": "server.network.physical_count", "name": "Physical NIC count", "value": inventory.get("network", {}).get("physical_count")},
    ]
    for gpu in inventory.get("gpu", {}).get("gpus", []): items.append({"key":"server.gpu.model", "name":"GPU model", "value":gpu.get("model")})
    for interface in inventory.get("network", {}).get("interfaces", []):
        if interface.get("classification") == "physical": items.append({"key":f"server.network.speed[{interface.get('ifname')}]", "name":f"NIC speed {interface.get('ifname')}", "value":interface.get("speed_mbps")})
    return {"template":name, "purpose":"Acceptance inventory mapping for later Zabbix monitoring", "items":items}
