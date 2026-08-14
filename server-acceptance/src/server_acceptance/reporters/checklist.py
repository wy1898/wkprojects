from pathlib import Path
def render_checklist(report, path):
    lines = ["Server Delivery Checklist", "=" * 28, ""]
    for r in report["validation_results"]:
        label = r.get("name") or r["component"]
        lines += [f"[{r['status']}] {label}", f"  Expected: {r.get('expected')}", f"  Actual: {r.get('actual')}", f"  Reason: {r.get('reason', r.get('message',''))}", f"  Evidence: {r.get('evidence')}", f"  Recommended Action: {r.get('recommendation','')}", ""]
    lines += [f"Overall Result: {report['status']}"]
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text("\n".join(lines), encoding="utf-8")
