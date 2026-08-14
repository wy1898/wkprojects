import json, tarfile
from pathlib import Path
def create_bundle(report, html_path, checklist_path, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as archive:
        files = {"inventory.json": report["inventory"], "validation.json": report["validation_results"], "acceptance.json": report}
        for name, data in files.items():
            path = output.parent / f".{output.stem}_{name}"; path.write_text(json.dumps(data, indent=2), encoding="utf-8"); archive.add(path, arcname=name); path.unlink()
        for path in (html_path, checklist_path):
            if path.exists(): archive.add(path, arcname=path.name)
