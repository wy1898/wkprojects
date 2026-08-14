# Linux服务器验收平台

Linux Server Acceptance Platform 是一个面向 Linux Server、GPU Server、AI Server 和 Kubernetes Node 的硬件验收与交付验证工具。

它把服务器交付前的流程组织为：

```text
Collectors -> Inventory -> Profile/Expectation -> ValidationEngine
           -> Acceptance Result -> JSON / HTML / Checklist / Bundle
```

项目定位是 deterministic server acceptance，不是 GPU benchmark、GPU stress test、GPU diagnostic 或监控平台。

## 应用场景

- Linux 服务器交付前的硬件清点与规格核对
- GPU 服务器数量、型号、显存、驱动和基础可用性验收
- AI 训练/推理节点的 CPU、内存、存储和网络验收
- Kubernetes Worker Node 上线前的基础环境预检查
- 生成可供工程师、交付人员和 CI 使用的验收报告

## 功能列表

- CPU、Memory、Storage、RAID、Network、GPU、OS、Kubernetes collectors
- `min` / `exact` 验收语义
- physical / loopback / virtual network 分类
- SMART/NVMe、RAID capability、NIC speed 等可选检查
- `generic`、`gpu_server`、`ai_server`、`k8s_node`、`demo` profiles
- CLI、中文 Flask WebUI
- JSON、静态 HTML、Checklist、Support Bundle
- Zabbix inventory mapping export
- 工具缺失、权限不足、WSL2 能力缺失时使用 `UNAVAILABLE`，不虚构硬件故障

## 架构说明

Collector 只负责获取事实；Inventory 保存实际硬件信息；Profile/Expectation 定义交付要求；ValidationEngine 负责比较；Reporter 负责输出；CLI 和 WebUI 都复用同一套核心服务。

```text
src/server_acceptance/
├── collectors/     CPU/Memory/Storage/RAID/Network/GPU/OS/K8s
├── models/         Inventory、Expectation、ValidationResult
├── validators/     ValidationEngine
├── services/       Acceptance、Runner、Bundle
├── reporters/      JSON、HTML、Checklist
├── integrations/   Zabbix mapping export
└── web.py          Flask WebUI
```

## 安装方式

```bash
make install
```

或手动执行：

```bash
python3 -m pip install -r requirements.txt
```

## 快速启动

查看全部命令：

```bash
make help
```

启动 WebUI：

```bash
make start
```

访问：<http://127.0.0.1:8000>

`make start` 会检查 Python、设置 `PYTHONPATH=src` 并启动 Flask WebUI。

如果不使用 Make：

```bash
PYTHONPATH=src python3 -m server_acceptance.web
```

## CLI 使用方式

```bash
make check
server-check inventory
server-check validate --profile generic
server-check validate --profile gpu_server
server-check validate --profile ai_server
server-check validate --profile k8s_node
server-check bundle --profile generic --output reports/support_bundle.tar.gz
```

原有 CLI 行为保持不变。

## Profile 说明

| Profile | 用途 |
|---|---|
| `demo` | 本地演示环境，适配常见 8GB WSL2 主机 |
| `generic` | 普通 Linux 服务器基础验收 |
| `gpu_server` | NVIDIA GPU 计算服务器验收 |
| `ai_server` | AI 训练/推理服务器验收 |
| `k8s_node` | Kubernetes Worker Node 上线前预检查 |

生产 profile 的要求不会因为本地演示机硬件较低而降低。

## 输出报告

`server-check validate` 和 WebUI 可以生成：

- JSON：机器可读的完整结果
- HTML：适合详细人工查看的静态报告
- Checklist：适合交付现场快速勾选
- Support Bundle：汇总 inventory、validation、acceptance 和报告文件

报告默认写入 `reports/`。示例合成数据保存在 [examples/gpu_server_demo.json](examples/gpu_server_demo.json)，不包含真实本机硬件信息。

## Zabbix 导出

项目不运行 Zabbix Server，也不连接外部 Zabbix；只导出后续监控使用的 inventory mapping：

```bash
server-check zabbix-template --profile generic --output reports/zabbix-template.json
```

## WebUI 截图位置说明

本仓库当前不提交真实主机截图，避免把本机硬件信息混入项目。运行 `make start` 后，可在浏览器访问首页和结果页进行截图；截图建议保存到项目外部或单独的展示素材目录。

## 测试

```bash
make test
```

测试覆盖 Runner、Collectors、ValidationEngine、Storage/Network/GPU 规则、报告、Zabbix mapping 和 WebUI 基础路由。

## 当前边界

不包含 Prometheus、AI 诊断、SSH 批量部署、自动修复、数据库、登录/RBAC、React/Vue、Kubernetes 集群管理或 Zabbix Server。本项目专注于 Linux 服务器硬件 Inventory、规格验收、交付检查和报告生成。
