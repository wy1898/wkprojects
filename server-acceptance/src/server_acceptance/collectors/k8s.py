from ..services.runner import CommandRunner

class KubernetesNodeCollector:
    """Optional node pre-checks; this does not manage a Kubernetes cluster."""
    def __init__(self, runner=None): self.runner = runner or CommandRunner()
    def collect(self):
        runtime = self._first_available((["containerd", "--version"], "containerd"), (["docker", "--version"], "docker"), (["crio", "--version"], "crio"))
        kubelet = self.runner.run(["kubelet", "--version"])
        kubectl = self.runner.run(["kubectl", "version", "--client", "--output=json"])
        return {"container_runtime": runtime, "kubelet": self._result(kubelet), "kubectl": self._result(kubectl), "status": "AVAILABLE" if runtime or kubelet.status == "AVAILABLE" or kubectl.status == "AVAILABLE" else "UNAVAILABLE"}
    def _first_available(self, *candidates):
        attempts=[]
        for command, name in candidates:
            result=self.runner.run(command); attempts.append(self._result(result) | {"tool":name})
            if result.status == "AVAILABLE": return {"name":name, "status":"AVAILABLE", "version":result.stdout, "attempts":attempts}
        return {"name":None, "status":"UNAVAILABLE", "attempts":attempts}
    def _result(self, result): return {"status":"AVAILABLE" if result.status == "AVAILABLE" else "UNAVAILABLE", "stdout":result.stdout, "stderr":result.stderr, "error":result.error}
