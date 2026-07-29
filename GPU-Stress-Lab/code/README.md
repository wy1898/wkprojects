# GPU 计算环境部署与压力测试平台

面向 Linux/WSL2 GPU 环境的终端运维工具，提供 GPU 信息查询、环境检查、实时监控和 CUDA 矩阵乘法压力测试。

## 当前版本

V2：在 V1 CLI 基础上增加 Flask Web Dashboard、实时图表、后台压力测试控制、日志和异常告警。

## 环境要求

- Linux 或 WSL2 Ubuntu
- Python 3.10 或更高版本
- 可用的 NVIDIA 驱动与 `nvidia-smi`
- CUDA 可用的 PyTorch（压力测试需要）
- Flask（Web Dashboard 需要）

安装基础依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

若 PyTorch 官方安装命令针对你的 CUDA 版本不同，请先按官方说明安装对应版本，再安装其余依赖。

## 使用方式

直接使用 Python 模块：

```bash
PYTHONPATH=src python -m gpu_platform --help
PYTHONPATH=src python -m gpu_platform info
PYTHONPATH=src python -m gpu_platform env
PYTHONPATH=src python -m gpu_platform monitor
PYTHONPATH=src python -m gpu_platform monitor --device 0 --interval 2
PYTHONPATH=src python -m gpu_platform stress
PYTHONPATH=src python -m gpu_platform stress --device 0 --duration 60 --size 2048 --interval 1
PYTHONPATH=src python -m gpu_platform web
PYTHONPATH=src python -m gpu_platform web --host 0.0.0.0 --port 5000 --device 0
```

安装项目后也可以直接使用入口命令：

```bash
python -m pip install .
gpu-platform info
gpu-platform env
gpu-platform monitor --device 0 --interval 2
gpu-platform stress --device 0 --duration 60 --size 2048 --interval 1
gpu-platform web
```

监控和压力测试均可使用 `Ctrl+C` 安全退出。压力测试会在结束时释放 CUDA Tensor 和缓存。

## Web Dashboard

启动服务：

```bash
./scripts/start.sh web --host 127.0.0.1 --port 5000 --device 0
```

浏览器访问 [http://localhost:5000](http://localhost:5000)。Dashboard 提供 GPU 状态卡片、利用率/温度/显存折线图、压力测试 Start/Stop 控制和 WARNING 告警区域。生产或局域网部署时可使用 `--host 0.0.0.0`，并在反向代理或防火墙层控制访问权限。

运行日志默认写入 `logs/gpu-platform.log`，压力测试历史默认写入 `logs/stress_history.json`，两者都可以通过环境变量指定目录/文件。

## Shell 启动

```bash
chmod +x scripts/start.sh
./scripts/start.sh --help
./scripts/start.sh info
./scripts/start.sh monitor --device 0 --interval 2
```

## 目录结构

```text
gpu-platform/
├── README.md
├── requirements.txt
├── pyproject.toml
├── scripts/start.sh
└── src/gpu_platform/
    ├── __init__.py
    ├── __main__.py
    ├── cli.py
    ├── api.py
    ├── alert.py
    ├── gpu.py
    ├── history.py
    ├── monitor.py
    ├── output.py
    ├── stress.py
    ├── utils.py
    └── web.py
templates/dashboard.html
static/css/style.css
static/js/dashboard.js
```

## 已知边界

- `nvidia-smi` 是 GPU 信息、监控和压力测试的前置条件。
- `output.py` 在 Rich 未安装时会自动降级为普通文本输出。
- PyTorch 必须具备 CUDA 支持，CPU 版本不能执行压力测试。
- Web 页面使用 Chart.js CDN，离线环境需要替换为本地静态资源。
