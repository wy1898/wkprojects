"""Standalone HTML output for sharing a diagnostic run without a web service."""

from __future__ import annotations

from html import escape
from pathlib import Path

from gpu_diagnostic.models.run import DiagnosticRun


class HTMLReporter:
    def write(self, run: DiagnosticRun, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"diagnostic_{run.run_id}.html"
        path.write_text(self.render(run), encoding="utf-8")
        return path

    def render(self, run: DiagnosticRun) -> str:
        findings = "".join(self._finding_html(item.to_dict()) for item in run.findings) or "<p>No diagnostic rule matched. This does not replace engineering review.</p>"
        os_name = escape(str(run.host_info.get("os_release", {}).get("PRETTY_NAME", "Unavailable")))
        return f"""<!doctype html><html><head><meta charset=\"utf-8\"><title>GPU Diagnostic Report</title>
<style>body{{font-family:Arial,sans-serif;max-width:1000px;margin:32px auto;color:#202124}} .status{{font-weight:bold}} article{{border:1px solid #ddd;padding:16px;margin:16px 0}} h3{{margin-top:0}} code{{white-space:pre-wrap}} </style>
</head><body><h1>GPU Diagnostic Report</h1><p><b>Run:</b> {escape(run.run_id)}<br><b>Host:</b> {escape(run.hostname)}<br><b>System:</b> {os_name}<br><b>Status:</b> <span class=\"status\">{escape(run.status.value)}</span><br><b>Findings:</b> {len(run.findings)}</p><h2>Findings</h2>{findings}</body></html>"""

    @staticmethod
    def _finding_html(finding: dict[str, object]) -> str:
        evidence = "".join(f"<li><b>{escape(str(item['source']))}</b>: {escape(str(item['matched']))}<br><small>{escape(str(item['detail']))}</small></li>" for item in finding["evidence"])  # type: ignore[index]
        causes = "".join(f"<li>{escape(str(item))}</li>" for item in finding["possible_causes"])  # type: ignore[index]
        recommendations = "".join(f"<li>{escape(str(item))}</li>" for item in finding["recommendations"])  # type: ignore[index]
        return f"<article><h3>[{escape(str(finding['severity']))}] {escape(str(finding['title']))}</h3><p>{escape(str(finding['description']))}</p><h4>Evidence</h4><ul>{evidence}</ul><h4>Possible causes</h4><ul>{causes}</ul><h4>Recommendations</h4><ul>{recommendations}</ul></article>"
