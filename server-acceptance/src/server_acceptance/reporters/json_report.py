from datetime import datetime, timezone
import json, uuid, socket
from ..models import Status
from ..services.acceptance import overall_status, recommendation

def build_report(inventory, expectation, results):
    overall = overall_status(results)
    values = [r.to_dict() | {"reason": r.message, "recommendation": recommendation(r)} for r in results]
    return {"run_id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(), "hostname": socket.gethostname(), "status": overall.value, "inventory": inventory.to_dict(), "expectations": expectation.to_dict(), "validation_results": values, "overall_status": overall.value}
def write_report(report, path):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(report, indent=2), encoding="utf-8")
