from server_acceptance.models import Inventory, Expectation
from server_acceptance.validators import ValidationEngine
from server_acceptance.collectors.raid import RaidCollector
from server_acceptance.services.runner import CommandResult

def test_storage_exact_and_type():
    inv=Inventory(storage={"devices":[{"type":"disk","transport":"nvme","size":"1T"},{"type":"disk","transport":"nvme","size":"1T"}]})
    results=ValidationEngine().validate(inv, Expectation.from_dict({"storage":{"count":{"exact":2},"type":{"exact":"nvme"},"min_capacity_gb":900}}))
    assert all(x.status.value == "PASS" for x in results)

def test_storage_type_mismatch():
    inv=Inventory(storage={"devices":[{"type":"disk","transport":"sata","size":"1T"}]})
    results=ValidationEngine().validate(inv, Expectation.from_dict({"storage":{"type":{"exact":"nvme"}}}))
    assert results[0].status.value == "FAIL"

def test_raid_tools_unavailable():
    class Missing:
        def run(self, command): return CommandResult(command, status="UNAVAILABLE", error="missing")
    assert RaidCollector(Missing()).collect()["status"] == "UNAVAILABLE"

def test_network_speed_mismatch():
    inv=Inventory(network={"physical_count":2,"interfaces":[{"classification":"physical","speed_mbps":10000},{"classification":"physical","speed_mbps":1000}]})
    result=ValidationEngine().validate(inv, Expectation.from_dict({"network":{"min_speed_mbps":10000}}))[0]
    assert result.status.value == "FAIL"
