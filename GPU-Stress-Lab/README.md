# GPU-Stress-Lab

面向 Linux/WSL2 的 GPU 信息查询、环境诊断、实时监控和 CUDA 矩阵乘法压力测试 CLI 工具。

## 项目背景

GPU 节点排障和稳定性验证需要同时观察设备信息、驱动/CUDA/PyTorch 状态，以及负载期间的显存、利用率、温度和功耗。该项目将这些操作封装为统一命令行，便于开发和运维场景快速复现与观察。

## 技术栈

- Python 3.10+
- PyTorch 2.0+（压力测试需要 CUDA 版本）
- `nvidia-smi`（信息查询、环境诊断和监控）
- Rich 13.7+（可选，用于表格和彩色输出）
- `argparse`、`subprocess`、`csv`、`time`
- `setuptools` / `pyproject.toml`

## 功能特点

- `info`：查询 GPU 型号、驱动、显存、利用率和温度。
- `env`：汇总操作系统、Python、`nvidia-smi`、PyTorch 和 CUDA 路径状态。
- `monitor`：按设备和刷新间隔持续显示 GPU 运行状态，支持 `Ctrl+C` 退出。
- `stress`：在指定 GPU 上执行 CUDA 矩阵乘法，记录迭代次数及峰值显存、利用率和温度。
- Rich 不可用时自动降级为普通文本输出。
- 同时提供 `python -m gpu_platform` 和安装后的 `gpu-platform` 入口。

## 环境要求

- Linux 或 WSL2 Ubuntu。
- Python 3.10 或更高版本。
- 可用的 NVIDIA 驱动和 `nvidia-smi`。
- `stress` 命令需要支持 CUDA 的 PyTorch；CPU 版 PyTorch 不能执行 GPU 压力测试。

## 安装步骤

```bash
cd GPU-Stress-Lab/code
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

如需安装项目命令入口：

```bash
python -m pip install .
```

PyTorch 应根据目标 CUDA/驱动组合选择对应的官方安装源。

## 使用方法

在 `GPU-Stress-Lab/code` 目录执行：

```bash
PYTHONPATH=src python -m gpu_platform --help
PYTHONPATH=src python -m gpu_platform info
PYTHONPATH=src python -m gpu_platform env
PYTHONPATH=src python -m gpu_platform monitor --device 0 --interval 2
PYTHONPATH=src python -m gpu_platform stress --device 0 --duration 60 --size 2048 --interval 1
```

也可以使用启动脚本：

```bash
chmod +x scripts/start.sh
./scripts/start.sh info
./scripts/start.sh stress --device 0 --duration 60 --size 2048
```

监控和压力测试均支持 `Ctrl+C` 安全退出。

## 示例输出

```text
=== GPU Platform Information ===
Status: available
GPU 0: NVIDIA ... | driver 550.xx | memory 1200/16384 MiB | utilization 8% | temperature 45 C

=== GPU 压力测试摘要 ===
运行时间: 60.00s
矩阵规模: 2048 x 2048
总迭代次数: 1234
峰值显存: 5200 MiB
峰值 GPU 利用率: 99%
是否正常结束: 是
```

设备型号、版本、指标和迭代次数随实际硬件与负载变化；示例仅展示格式。

## 项目结构

```text
GPU-Stress-Lab/
├── README.md
└── code/
    ├── README.md
    ├── pyproject.toml
    ├── requirements.txt
    ├── scripts/start.sh
    └── src/gpu_platform/
        ├── __main__.py    # python -m 入口
        ├── cli.py         # 子命令和参数
        ├── gpu.py         # GPU 信息和环境检查
        ├── monitor.py     # 实时监控
        ├── stress.py      # CUDA 压力测试
        └── output.py      # Rich/文本输出
```

## 已知限制

- 依赖本机 NVIDIA 驱动和 `nvidia-smi`，不提供模拟 GPU 数据。
- 压力测试会实际占用 GPU 计算资源，运行前应确认设备和矩阵规模。

