from server_acceptance.collectors import SystemCollector
from server_acceptance.services.runner import CommandResult

class FakeRunner:
    def run(self, command, timeout=None):
        if command[0] == "lscpu":
            return CommandResult(command, '{"lscpu":[{"field":"Socket(s):","data":"2"},{"field":"Model name:","data":"Fixture CPU"},{"field":"CPU(s):","data":"8"}]}')
        return CommandResult(command, status="UNAVAILABLE", error="fixture unavailable")

def test_cpu_collector_uses_runner():
    inventory = SystemCollector(FakeRunner()).collect()
    assert inventory.cpu["sockets"] == 2
    assert inventory.cpu["model"] == "Fixture CPU"
