#!/usr/bin/env bash

# 项目统一启动脚本：将参数原样交给 Python CLI。
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

exec python3 -m gpu_platform "$@"
