from ..models import Status

def overall_status(results):
    statuses = [x.status for x in results]
    if Status.FAIL in statuses: return Status.FAIL
    if any(x in statuses for x in (Status.WARNING, Status.UNAVAILABLE, Status.ERROR)): return Status.WARNING
    return Status.PASS

def recommendation(result):
    if result.status == Status.PASS:
        return {"CPU": "No action required.", "Memory": "Memory capacity satisfies the configured requirement.", "GPU": "GPU inventory satisfies the configured requirement.", "Storage": "Storage inventory satisfies the configured requirement.", "Network": "Network interfaces satisfy the configured requirement.", "RAID": "RAID check completed successfully.", "OS": "OS requirements are satisfied."}.get(result.component, "No action required.")
    text = (result.message or "").lower()
    if result.status == Status.UNAVAILABLE:
        if "smart" in text: return "SMART health could not be determined because smartctl is unavailable. Install smartmontools or run validation on a host exposing disk health information."
        if "raid" in text: return "RAID capability could not be determined because no supported RAID management utility is available."
        if "kubelet" in text: return "Kubernetes node status could not be determined because kubelet is not installed or accessible."
        if "kubectl" in text: return "Kubernetes version could not be determined because kubectl is not installed or accessible."
        return "Required validation could not be performed because a tool, permission, or platform capability is unavailable. Install the required tool or rerun on a host exposing the information."
    if result.component == "GPU":
        if "model" in text: return "Verify the installed GPU model against the deployment specification."
        if "memory" in text or "vram" in text: return "Verify GPU memory capacity against the deployment specification."
        return "Verify GPU inventory against the deployment specification."
    if result.component == "Memory": return "Verify installed memory capacity and compare it with the deployment specification."
    if result.component == "Network":
        if "speed" in text: return "Verify NIC capability, cable connection and link negotiation."
        return "Verify physical NIC installation and network adapter inventory."
    if result.component == "Storage": return "Check disk installation and storage configuration."
    if result.component == "RAID": return "Check RAID member disk status and controller logs."
    if result.component == "CPU": return "Verify CPU topology against the deployment specification."
    if result.component == "OS": return "Verify the installed operating system and architecture against the deployment specification."
    return "Review the expected configuration and collected evidence."
