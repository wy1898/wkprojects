# GPU Diagnostic Platform

面向 Linux NVIDIA GPU 服务器的、以证据为基础的自动化诊断工具。

GPU Diagnostic Platform 是一个基于 Python 的命令行工具，用于在 GPU 服务器出现异常后，采集主机、NVIDIA、PCIe、驱动、CUDA、PyTorch 以及内核日志信息。工具通过一组可解释的规则进行分析，并生成包含证据、可能原因和建议排查步骤的诊断结果。

本项目定位为聚焦单机故障排查的开源工程工具，不是商业化服务器管理平台、实时监控系统，也不是自动硬件维修工具。

## 核心诊断链路

```text
gpu-diag diagnose
        |
        v
Collectors（Linux/NVIDIA 命令）
        |
        v
DiagnosticSnapshot
        |
        v
RuleEngine / Analyzer
        |
        v
Finding（Evidence → Possible Causes → Recommendations）
        |
        v
DiagnosticRun
        |
        v
JSON 报告 + 静态 HTML 报告
```

Collector 负责获取事实并保存命令输出、错误信息和退出状态；Snapshot 是采集层与分析层之间的数据边界；Rule Engine 通过关键词、正则表达式和多个独立信号组合进行分析；Finding 描述诊断方向并引用具体证据；DiagnosticRun 表示一次完整诊断任务；Reporter 输出 JSON 和独立 HTML 文件。

## 当前已实现的功能

- 通过 `nvidia-smi` 采集 GPU 型号、数量、UUID、PCI Bus ID、驱动、CUDA、显存、温度、ECC 和 Persistence Mode。
- 通过 `lspci -nn` 枚举 PCIe 设备。
- 通过 `lsmod` 检查 NVIDIA 内核模块。
- 通过 `nvcc --version` 检查 CUDA Toolkit。
- 检查当前 Python 环境中的 PyTorch CUDA 可用性。
- 通过 `dmesg -T` 采集内核日志并按关键字筛选。
- 采集 hostname、内核版本、架构和 `/etc/os-release`。
- 结构化 Evidence：`source`、`matched`、`detail`。
- 关键词、正则表达式和多信号组合规则。
- 配置温度阈值、预期 GPU 数量、日志关键字和预期 Persistence Mode。
- JSON 报告、静态 HTML 报告和 CLI。
- Python `unittest` 回归测试及故障日志 fixtures。

## 当前支持的诊断场景

规则库当前包含 15 条规则：

- PCIe 总线上未检测到 NVIDIA GPU。
- PCIe 可见 NVIDIA GPU，但 `nvidia-smi` 失败。
- Xid 13、Xid 31、Xid 48、Xid 79。
- NVIDIA 驱动模块未加载。
- CUDA Toolkit 编译器不可用。
- PyTorch CUDA 不可用。
- Driver/CUDA Runtime 兼容性错误。
- PCIe/AER 错误。
- GPU 温度超过配置阈值。
- 不可纠正 ECC 错误。
- Persistence Mode 与配置不一致。
- 实际 GPU 数量低于预期。

规则提供可能原因和建议措施，不会将命中结果直接表述为绝对硬件故障。

## 基于证据的诊断

工具不会简单地把“命令失败”解释为“GPU 损坏”。例如：

```text
lspci 检测到 NVIDIA 设备
        +
nvidia-smi 执行失败
        |
        v
可能问题：NVIDIA 驱动与 GPU 之间的通信异常
```

每条 Finding 都遵循：

```text
Evidence → Possible Causes → Recommendations
```

因此输出的是排查方向和证据保留结果，而不是自动维修动作或最终硬件判定。

## 项目结构

```text
gpu-diagnostic/
├── config.yaml
├── scripts/gpu-diag.sh
├── src/gpu_diagnostic/
│   ├── analyzer/
│   ├── cli/
│   ├── collector/
│   ├── knowledge/
│   ├── models/
│   ├── reporter/
│   ├── services/
│   └── utils/
├── tests/
│   ├── fixtures/
│   ├── test_analyzer.py
│   ├── test_phase2.py
│   └── test_rule_engine.py
├── pyproject.toml
├── setup.py
└── requirements.txt
```

`collector/` 负责 Linux/NVIDIA 证据采集；`models/` 定义 Snapshot、Finding、Run 等数据模型；`analyzer/` 执行规则；`knowledge/rules.yaml` 保存规则库；`reporter/` 生成 JSON 和 HTML；`services/` 编排完整流程；`cli/` 提供命令行入口。

## 环境要求与安装

- Python 3.10 或更高版本。
- 目标运行环境为 Linux 主机。
- 对应检查需要 `nvidia-smi`、`lspci`、`lsmod`、`dmesg`；`nvcc` 和 PyTorch 为可选检查项。

当前项目没有第三方 Python 运行时依赖。命令不存在或权限不足时，错误会保存到 Snapshot，不会使完整诊断任务中断。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## CLI 使用方式

```bash
gpu-diag --help
gpu-diag collect
gpu-diag diagnose
gpu-diag diagnose --expected-gpus 4
gpu-diag diagnose --output-dir reports/server-01
./scripts/gpu-diag.sh diagnose
```

当前 CLI 输出类似：

```text
Diagnostic Summary:
Status: WARNING
Findings: 1
Findings:
1. [WARNING] CUDA toolkit compiler unavailable
JSON Report: reports/diagnostic_<run-id>.json
HTML Report: reports/diagnostic_<run-id>.html
```

`PASS` 表示没有已实现规则命中当前 Snapshot，不代表所有潜在问题都已排除。

## 配置文件

项目根目录的 `config.yaml`：

```yaml
temperature_threshold: 85
expected_gpu_count: null
expected_persistence_mode: null
log_keywords: [NVRM, Xid, PCI, AER]
```

支持的配置项：

- `temperature_threshold`：高温规则使用的采样温度阈值。
- `expected_gpu_count`：可选的预期 GPU 数量；也可用 `--expected-gpus` 覆盖。
- `expected_persistence_mode`：与 `nvidia-smi` 报告值进行比较。
- `log_keywords`：LogCollector 筛选 `dmesg` 的关键字。

## 报告

每次诊断生成两个文件：

- JSON：包含 run ID、时间、主机、状态、Snapshot、Collector 结果和结构化 Finding。
- 静态 HTML：展示主机信息、状态、Finding、Evidence、Possible Causes 和 Recommendations。

HTML 是独立文件，不是 Flask 应用、HTTP 服务或 Web Dashboard。

## 测试

当前仓库包含 11 项测试和多种故障日志 fixtures。运行：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

测试覆盖规则加载、关键词/正则匹配、PCIe 与 `nvidia-smi` 多源逻辑、Xid、GPU 数量、CUDA/PyTorch、配置、DiagnosticRun 状态、HTML 生成和 Persistence Mode。

## 与 GPU-Stress-Lab 的关系

GPU-Stress-Lab 负责施加 GPU 工作负载、实时观察温度/利用率/显存并展示压力测试结果。GPU Diagnostic Platform 在异常出现后采集 Linux/NVIDIA 证据、关联信号并生成排查报告。

```text
GPU-Stress-Lab：复现或观察异常
        |
        v
GPU Diagnostic Platform：采集证据并给出排查方向
```

本项目不会重新实现持续监控或压力测试。

## 设计原则

1. 先有证据，再形成结论。
2. 多信号优于单命令假设。
3. 使用可能原因，而不是绝对硬件结论。
4. 优先使用 Linux/NVIDIA 原生工具。
5. 分离采集、分析、模型和报告。
6. 同时提供机器可读和人类可读报告。
7. 缺失命令和权限错误也要保留为证据。
8. 默认只进行观察和采集，不执行高风险修改。

## 范围与限制

- 主要面向单机 Linux NVIDIA GPU 环境。
- WSL2、容器或受限环境可能限制 PCIe 和内核驱动检查。
- 工具提供排查方向，不认证硬件已经失效。
- 不会自动重置 GPU、卸载驱动、重启主机或修改系统配置。
- 当前没有实时监控、Web Dashboard、远程管理、分布式诊断、AI 诊断或云服务。
- `nvcc` 和 PyTorch 检查取决于当前环境是否安装。
- `PASS` 仅表示当前规则未匹配。

## 未来计划

以下均为尚未实现的方向：

- 更多 NVIDIA Xid 和 PCIe 规则。
- 更强的跨来源故障关联。
- 诊断包导出与脱敏。
- 服务器验收或基线模式。
- 可选的报告历史管理。
- 边界明确的远程诊断流程。

## License

当前仓库尚未包含 License 文件。如需公开发布并定义复用和贡献条款，请另行添加合适的开源许可证。

