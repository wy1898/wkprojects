# wkprojects

面向 CUDA 开发工程师 / GPU 工程岗位的项目集合，集中展示 GPU 环境验证、GPU 压力测试与 Slurm 集群作业管理方向的 Python/Linux 实践。

## 项目简介

### [gpu-validator](gpu-validator/)

GPU 计算环境验证工具：检查 NVIDIA GPU、CUDA Toolkit、PyTorch CUDA、Docker GPU 容器运行时，并运行矩阵乘法基准测试，生成终端和 JSON 报告。

### [GPU-Stress-Lab](GPU-Stress-Lab/)

Linux/WSL2 GPU 诊断与压力测试 CLI：提供 GPU 信息查询、环境检查、实时监控和可配置 CUDA 矩阵乘法压力测试。

### [slurm tool](slurm%20tool/)

Slurm 作业管理 CLI：查询作业和节点、提交/取消作业、查看历史，并通过解析器和格式化器将 Slurm 输出转为统一终端表格。

## 技术方向

- CUDA / PyTorch CUDA 运行时检查与 GPU 计算基准
- NVIDIA 驱动、`nvidia-smi`、CUDA Toolkit 与容器 GPU 环境
- GPU 利用率、显存、温度、功耗监控
- CUDA 矩阵乘法压力测试与运行指标采集
- Linux/WSL2 命令行工具开发与 subprocess 集成
- Slurm 集群作业、节点和 GPU 资源管理
- Python 模块化设计、数据模型、输出格式化和错误处理

三个项目均保留原有代码逻辑；本文档用于说明当前代码能力和运行边界，示例中的硬件指标与作业信息均为格式示意。

