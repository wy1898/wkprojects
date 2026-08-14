from pathlib import Path
from server_acceptance.collectors.system import classify_interface, _network_inventory

def test_loopback_excluded(tmp_path):
    assert classify_interface({"ifname": "lo", "flags": ["LOOPBACK"]}, str(tmp_path)) == "loopback"

def test_physical_uses_sysfs_device(tmp_path):
    (tmp_path / "eth0" / "device").mkdir(parents=True)
    assert classify_interface({"ifname": "eth0", "flags": ["BROADCAST"]}, str(tmp_path)) == "physical"

def test_wsl_ethernet_fallback_is_physical(tmp_path):
    assert classify_interface({"ifname": "eth0", "flags": ["BROADCAST"], "link_type": "ether"}, str(tmp_path)) == "physical"

def test_bridge_is_virtual_container(tmp_path):
    (tmp_path / "docker0" / "bridge").mkdir(parents=True)
    assert classify_interface({"ifname": "docker0", "flags": ["BROADCAST"]}, str(tmp_path)) == "virtual/container"

def test_network_inventory_counts_physical_only(tmp_path, monkeypatch):
    monkeypatch.setattr("server_acceptance.collectors.system.classify_interface", lambda item: {"lo":"loopback", "eth0":"physical", "docker0":"virtual/container"}[item["ifname"]])
    result = _network_inventory([{"ifname":"lo"}, {"ifname":"eth0"}, {"ifname":"docker0"}])
    assert result["physical_count"] == 1
    assert result["status"] == "AVAILABLE"
