# gpu-validator

面向 NVIDIA GPU 计算环境的验证工具，用于检查 GPU、CUDA Toolkit、PyTorch CUDA、Docker/NVIDIA Container Runtime，并执行一个可配置规模的 CUDA 矩阵乘法基准测试，最终输出终端摘要和 JSON 报告。

## 项目背景

GPU 应用部署通常同时依赖驱动、CUDA Toolkit、Python/PyTorch 和容器运行时。该项目将这些依赖拆分为独立检查器，再由 `ValidationRunner` 统一编排，帮助定位环境是否满足 GPU 计算任务的运行条件。

## 技术栈

- Python 3.10+
- NVIDIA `nvidia-smi` / CUDA Toolkit `nvcc`
- PyTorch（用于 CUDA 运行时检查和矩阵乘法基准）
- Docker、NVIDIA Container Toolkit（用于容器 GPU 检查）
- 标准库：`subprocess`、`dataclasses`、`json`、`pathlib`

## 功能特点

- 查询 GPU 型号、显存、驱动、CUDA 版本、温度和功耗。
- 检查 `nvcc` 与 Python 运行时版本。
- 检查 PyTorch 是否可用及其 CUDA 设备信息。
- 检查 Docker daemon、NVIDIA Container Runtime，并运行 CUDA GPU 容器验证。
- 执行同步的 `torch.matmul` GPU 基准测试并统计耗时。
- 统一输出 PASS / WARNING / FAILED 结果，并保存结构化 JSON 报告。

## 环境要求

- Linux 或具备对应 NVIDIA 工具链的环境。
- NVIDIA 驱动与 `nvidia-smi`；CUDA 检查还需要 `nvcc`。
- PyTorch（未安装时基准测试会跳过；CUDA 不可用时相关检查会失败或跳过）。
- Docker 与 NVIDIA Container Toolkit（Docker 检查依赖这些组件）。

## 安装步骤

```bash
cd gpu-validator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

`requirements.txt` 当前没有固定运行时依赖；PyTorch 应根据目标 NVIDIA 驱动和 CUDA 版本按官方方式安装。

## 使用方法

```bash
cd gpu-validator
python -m src.main
```

程序会在终端打印检查结果，并生成 `reports/gpu_validation_report.json`。基准测试默认使用 `1024 x 1024` 矩阵，当前入口未暴露命令行参数。

## 示例输出

```text
GPU Environment Validation Report
====================================
gpu: PASS - GPU detected
cuda: PASS - CUDA Toolkit 12.4 detected; Python 3.10.14
pytorch: PASS - PyTorch 2.x; CUDA runtime 12.x; GPU NVIDIA ...
docker: PASS - Docker GPU container validation passed
benchmark: PASS - 1024x1024 torch.matmul completed in 3.421 ms
final_result: PASS - All validation checks passed
====================================
```

实际版本、设备名称和耗时取决于本机环境；以上仅展示输出格式。

## 项目结构

```text
gpu-validator/
├── README.md
├── requirements.txt
├── reports/
│   └── .gitkeep
├── tests/
│   └── .gitkeep
└── src/
    ├── main.py             # CLI 入口
    ├── validator.py        # 检查流程编排
    ├── gpu_checker.py      # nvidia-smi GPU 检查
    ├── cuda_checker.py     # nvcc 检查
    ├── torch_checker.py    # PyTorch CUDA 检查
    ├── docker_checker.py   # Docker GPU 容器检查
    ├── benchmark.py        # CUDA 矩阵乘法基准
    ├── report.py           # 终端/JSON 输出
    ├── models.py           # 数据模型
    └── utils.py
```

