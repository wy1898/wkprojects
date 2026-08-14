import argparse, json
from pathlib import Path
from ..collectors import SystemCollector
from ..collectors.raid import RaidCollector
from ..collectors.storage import StorageHealthCollector
from ..models import Expectation
from ..reporters import build_report, write_report
from ..reporters.html import render_html
from ..reporters.checklist import render_checklist
from ..services.bundle import create_bundle
from ..validators import ValidationEngine
from ..integrations.zabbix import build_template

def _config(args):
    import yaml
    path = Path(args.config)
    if args.profile: path = Path("config/profiles") / f"{args.profile}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))
def main(argv=None):
    p=argparse.ArgumentParser(prog="server-check"); sub=p.add_subparsers(dest="command", required=True)
    sub.add_parser("inventory")
    v=sub.add_parser("validate"); v.add_argument("--config", default="config/default.yaml"); v.add_argument("--profile"); v.add_argument("--output", type=Path); v.add_argument("--html", type=Path); v.add_argument("--checklist", type=Path)
    b=sub.add_parser("bundle"); b.add_argument("--config", default="config/default.yaml"); b.add_argument("--profile"); b.add_argument("--output", type=Path, default=Path("reports/support_bundle.tar.gz"))
    z=sub.add_parser("zabbix-template"); z.add_argument("--profile", default="generic"); z.add_argument("--output", type=Path, default=Path("reports/zabbix-template.json"))
    args=p.parse_args(argv)
    inv=SystemCollector().collect()
    if args.command == "zabbix-template":
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(build_template(inv.to_dict()), indent=2), encoding="utf-8"); print(json.dumps(build_template(inv.to_dict()), indent=2)); return 0
    inv.raid = RaidCollector().collect()
    inv.storage["health"] = StorageHealthCollector().collect(inv.storage.get("devices", []) if isinstance(inv.storage, dict) else inv.storage)
    if args.command in ("validate", "bundle") and getattr(args, "profile", None) == "k8s_node":
        from ..collectors.k8s import KubernetesNodeCollector
        inv.k8s = KubernetesNodeCollector().collect()
    if args.command == "inventory": print(json.dumps(inv.to_dict(), indent=2)); return 0
    expectation=Expectation.from_dict(_config(args)); results=ValidationEngine().validate(inv, expectation); report=build_report(inv, expectation, results)
    out=args.output if hasattr(args, "output") and args.output and args.command != "bundle" else Path("reports/latest.json")
    write_report(report, out)
    html_path = args.html if hasattr(args, "html") and args.html else out.with_suffix(".html")
    checklist_path = args.checklist if hasattr(args, "checklist") and args.checklist else out.with_suffix(".checklist.txt")
    render_html(report, html_path); render_checklist(report, checklist_path)
    if args.command == "bundle": create_bundle(report, html_path, checklist_path, args.output)
    print(json.dumps(report, indent=2)); return 0 if report["status"] != "FAIL" else 1
