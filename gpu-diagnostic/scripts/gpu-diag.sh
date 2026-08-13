#!/usr/bin/env bash
# Thin server-friendly launcher; installation via pip also provides gpu-diag.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
exec python3 -m gpu_diagnostic.cli.main "$@"
