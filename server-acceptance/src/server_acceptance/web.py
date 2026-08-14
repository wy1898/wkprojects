"""Small Flask presentation layer for the Server Acceptance Platform."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .collectors import RaidCollector, SystemCollector
from .collectors.storage import StorageHealthCollector
from .models import Expectation
from .reporters import build_report, write_report
from .reporters.checklist import render_checklist
from .reporters.html import render_html
from .validators import ValidationEngine

PROFILES = ("demo", "generic", "gpu_server", "ai_server", "k8s_node")
PROFILE_LABELS = {
    "demo": "演示环境",
    "generic": "通用服务器",
    "gpu_server": "GPU服务器",
    "ai_server": "AI服务器",
    "k8s_node": "Kubernetes节点",
}
PROFILE_DESCRIPTIONS = {
    "demo": "适用于本地演示环境，使用较低但明确的验收要求。",
    "generic": "适用于普通 Linux 服务器基础验收。",
    "gpu_server": "适用于 NVIDIA GPU 计算节点验收。",
    "ai_server": "适用于 AI 训练/推理环境验收。",
    "k8s_node": "适用于 Kubernetes Worker Node 环境验收。",
}


def _project_root(project_root: str | Path | None = None) -> Path:
    return Path(project_root).resolve() if project_root else Path(__file__).resolve().parents[2]


def _load_profile(root: Path, profile: str) -> dict[str, Any]:
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}")
    import yaml

    path = root / "config" / "profiles" / f"{profile}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def run_validation(profile: str, project_root: str | Path | None = None) -> dict[str, Any]:
    """Run the same acceptance pipeline used by the CLI and return its report."""
    root = _project_root(project_root)
    inventory = SystemCollector().collect()
    inventory.raid = RaidCollector().collect()
    if isinstance(inventory.storage, dict):
        inventory.storage["health"] = StorageHealthCollector().collect(
            inventory.storage.get("devices", [])
        )
    if profile == "k8s_node":
        from .collectors.k8s import KubernetesNodeCollector

        inventory.k8s = KubernetesNodeCollector().collect()

    expectation = Expectation.from_dict(_load_profile(root, profile))
    results = ValidationEngine().validate(inventory, expectation)
    if profile == "demo":
        # Demo is intentionally a presentation profile. Optional host capabilities
        # remain visible but do not make a local demo fail or warn.
        results = [
            result for result in results
            if not (result.status.value == "UNAVAILABLE" and result.component in {"RAID", "Storage"})
        ]
    report = build_report(inventory, expectation, results)
    reports_dir = root / "reports"
    json_path = reports_dir / f"web_{report['run_id']}.json"
    html_path = reports_dir / f"web_{report['run_id']}.html"
    checklist_path = reports_dir / f"web_{report['run_id']}.checklist.txt"
    report["profile"] = profile
    report["report_files"] = {
        "json": json_path.name,
        "html": html_path.name,
        "checklist": checklist_path.name,
    }
    write_report(report, json_path)
    render_html(report, html_path)
    render_checklist(report, checklist_path)
    return report


def create_app(project_root: str | Path | None = None):
    try:
        from flask import Flask, redirect, render_template, request, send_from_directory, url_for
    except ImportError as exc:  # pragma: no cover - depends on optional environment dependency
        raise RuntimeError("Flask is required. Install it with: python -m pip install Flask") from exc

    root = _project_root(project_root)
    reports_dir = root / "reports"
    app = Flask(__name__, template_folder=str(root / "templates"))
    app.config["PROJECT_ROOT"] = root

    @app.get("/")
    def index():
        return render_template("index.html", profiles=PROFILES, labels=PROFILE_LABELS, descriptions=PROFILE_DESCRIPTIONS)

    @app.post("/validate")
    def validate():
        profile = request.form.get("profile", "generic")
        if profile not in PROFILES:
            return render_template("error.html", message="Unknown profile"), 400
        try:
            report = run_validation(profile, root)
        except Exception as exc:
            app.logger.exception("Validation failed")
            return render_template("error.html", message=str(exc)), 500
        return render_template("results.html", report=report, components=_component_rows(report), labels=PROFILE_LABELS)

    @app.get("/reports/<path:filename>")
    def reports(filename):
        return send_from_directory(reports_dir, filename, as_attachment=True)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "server-acceptance-web"}

    return app


def _component_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep the UI stable even when a profile does not configure every component."""
    by_component = {item["component"]: item for item in report.get("validation_results", [])}
    rows = []
    for name in ("CPU", "Memory", "GPU", "Storage", "Network", "OS", "RAID", "Kubernetes"):
        item = by_component.get(name)
        if item:
            rows.append(item)
        else:
            rows.append({
                "component": name,
                "status": "UNAVAILABLE",
                "expected": "未配置",
                "actual": "未检测",
                "evidence": "该模板没有配置此组件的验收规则。",
                "reason": "当前模板未定义此组件检查。",
                "recommendation": "如需验收，请在对应模板中增加配置。",
            })
    return rows


def main() -> None:
    app = create_app()
    print("Server Acceptance Web UI listening on http://127.0.0.1:8000", flush=True)
    app.run(host="127.0.0.1", port=8000, debug=False)


if __name__ == "__main__":
    main()
