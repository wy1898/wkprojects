from server_acceptance.integrations.zabbix import build_template
from server_acceptance.models import Inventory, Expectation
from server_acceptance.validators import ValidationEngine

def test_zabbix_template_maps_core_optional_metrics():
    data = build_template(Inventory(cpu={"cores": 8}, gpu={"gpus":[{"model":"A100"}]}).to_dict())
    keys = {item["key"] for item in data["items"]}
    assert "server.cpu.cores" in keys
    assert "server.gpu.count" in keys

def test_k8s_optional_unavailable_is_not_fail():
    inv = Inventory(k8s={"container_runtime":{"status":"UNAVAILABLE"}, "kubelet":{"status":"UNAVAILABLE"}, "kubectl":{"status":"UNAVAILABLE"}})
    results = ValidationEngine().validate(inv, Expectation.from_dict({"kubernetes":{"container_runtime":"optional","kubelet":"optional","kubectl":"optional"}}))
    assert results and all(x.status.value == "UNAVAILABLE" for x in results)
