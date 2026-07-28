# slurm tool

面向 Slurm 集群的 Python 命令行工具，封装作业查询、节点查询、作业提交、取消和历史作业查询，并将 Slurm 命令输出解析为结构化模型后格式化展示。

## 项目背景

GPU 集群通常通过 Slurm 进行资源调度。相比直接记忆多个 Slurm 命令，该工具提供统一 CLI 和稳定的解析/格式化层，便于后续扩展 GPU 资源过滤、作业状态监控和集群运维能力。

## 技术栈

- Python 3.10+（代码使用现代类型标注）
- Slurm CLI：`squeue`、`sinfo`、`sbatch`、`scancel`、`sacct`
- Python 标准库：`argparse`、`subprocess`、`dataclasses`、`re`

## 功能特点

- `jobs`：列出当前作业。
- `nodes`：列出计算节点及 GPU/CPU 数量。
- `submit <script>`：提交作业脚本并解析 Job ID。
- `cancel <job_id>`：取消指定作业。
- `history`：列出历史作业。
- 对 Slurm 命令缺失、超时、非零退出和输出格式错误提供统一错误处理。
- 通过数据模型、解析器和格式化器分离外部命令、业务数据和终端展示。

## 环境要求

- Python 3.10 或更高版本。
- 已配置的 Slurm 客户端环境和访问权限。
- 使用的命令应位于 `PATH`：`squeue`、`sinfo`、`sbatch`、`scancel`、`sacct`。

## 安装步骤

```bash
cd "slurm tool"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

当前 `requirements.txt` 为空，项目仅依赖 Python 标准库。

## 使用方法

在项目目录执行：

```bash
python -m src.cli jobs
python -m src.cli nodes
python -m src.cli submit path/to/job.sh
python -m src.cli cancel 10001
python -m src.cli history
```

也可以直接执行入口文件：

```bash
python src/cli.py jobs
```

真实命令会直接访问当前 Slurm 环境；提交和取消作业属于有副作用的操作，请先确认目标集群和 Job ID。

## 示例输出

```text
JOBID | NAME     | STATE   | USER  | PARTITION | NODE
------+----------+---------+-------+-----------+------
1001  | analysis | RUNNING | alice | compute   | node01

Job submitted successfully.
Job ID: 10001
```

示例中的作业和节点信息为展示格式，不代表真实集群状态。

## 项目结构

```text
slurm tool/
├── README.md
├── requirements.txt
├── tests/
│   └── .gitkeep
└── src/
    ├── cli.py       # 命令行入口
    ├── slurm.py     # Slurm subprocess 客户端
    ├── parser.py    # 命令输出解析
    ├── formatter.py # 表格和结果格式化
    ├── models.py    # Job/Node 数据模型
    └── utils.py
```

## 当前边界

CLI 默认连接真实 Slurm 环境；`SlurmClient` 内部保留 `use_mock` 数据源能力，但当前命令行入口未提供 mock 参数。项目目前没有打包配置或自动化测试实现。

