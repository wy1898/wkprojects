# GPU Diagnostic Platform

Evidence-driven diagnostics for Linux NVIDIA GPU servers.

GPU Diagnostic Platform is a Python-based command-line tool for collecting host, NVIDIA, PCIe, driver, CUDA, PyTorch, and kernel-log evidence after a GPU server shows abnormal behavior. It applies a small, explainable rule set and produces findings with their supporting evidence, possible causes, and recommended next checks.

The project is intentionally a focused single-host diagnostic utility. It is not a commercial fleet-management product, a real-time monitoring system, or an automatic hardware-repair tool.

## What problem does it solve?

When a Linux GPU server has an incident, an engineer commonly needs to collect and correlate several independent facts:

- Is an NVIDIA GPU visible on the PCIe bus?
- Does `nvidia-smi` work, and which GPU/driver/runtime values does it report?
- Is the NVIDIA kernel module loaded?
- Is the CUDA Toolkit available?
- Can the current Python environment use CUDA through PyTorch?
- Did the kernel log an NVRM Xid, PCIe, or AER event?
- Is the detected GPU inventory smaller than the expected inventory?

This tool automates that first evidence-gathering pass and turns it into a repeatable diagnostic artifact. It does not claim that one log line proves a physical component has failed.

## Diagnostic chain

```text
gpu-diag diagnose
        |
        v
Collectors (Linux/NVIDIA commands)
        |
        v
DiagnosticSnapshot
        |
        v
RuleEngine / Analyzer
        |
        v
Finding (Evidence -> Possible Causes -> Recommendations)
        |
        v
DiagnosticRun
        |
        v
JSON report + static HTML report
```

The separation is deliberate:

- Collectors acquire facts and preserve command output, errors, and exit status.
- `DiagnosticSnapshot` provides a normalized boundary between collection and analysis.
- The Rule Engine evaluates keywords, regular expressions, and combinations of independent signals.
- A `Finding` describes a diagnostic direction and cites the evidence that caused the rule to match.
- `DiagnosticRun` represents one complete operator-triggered diagnosis.
- Reporters make the same run available as machine-readable JSON and a standalone human-readable HTML file.

## Implemented capabilities

The following capabilities are present in the current codebase:

- NVIDIA GPU information through `nvidia-smi`.
- GPU count, GPU UUID, PCI Bus ID, driver version, CUDA version, memory, temperature, ECC counter, and Persistence Mode collection.
- PCIe device enumeration through `lspci -nn`.
- NVIDIA kernel-module inspection through `lsmod`.
- CUDA Toolkit check through `nvcc --version`.
- PyTorch CUDA availability check in the active Python interpreter.
- Kernel log collection through `dmesg -T` with configurable keyword filtering.
- Host identity collection: hostname, kernel version, architecture, and `/etc/os-release`.
- Structured `Evidence` objects containing `source`, `matched`, and `detail`.
- Rule matching using keywords, regular expressions, and multiple signal combinations.
- Configurable temperature threshold, expected GPU count, log keywords, and expected Persistence Mode.
- JSON report generation.
- Standalone static HTML report generation; no web server is included.
- CLI commands for collection and diagnosis.
- Python `unittest` regression tests and realistic-format diagnostic log fixtures.

## Supported diagnostic scenarios

The rule library currently contains 15 rules covering these directions:

- NVIDIA GPU not detected on the PCIe bus.
- NVIDIA GPU visible on PCIe but `nvidia-smi` fails.
- Xid 13 GPU exception.
- Xid 31 GPU memory/page-fault direction.
- Xid 48 ECC-related event.
- Xid 79 GPU communication loss / “fallen off the bus”.
- NVIDIA driver module not loaded.
- CUDA Toolkit compiler unavailable.
- PyTorch CUDA unavailable.
- Driver/CUDA runtime compatibility error.
- PCIe or AER error.
- Sampled GPU temperature above the configured threshold.
- Uncorrectable ECC counter reported by `nvidia-smi`.
- Persistence Mode differs from the configured expectation.
- Detected GPU count is below the operator-provided expected inventory.

These rules express possible causes such as PCIe instability, driver state, power delivery, workload behavior, environment configuration, or hardware instability. They do not convert a rule match into an absolute hardware verdict.

## Evidence-based diagnosis

The project is designed to avoid single-command conclusions. For example:

```text
lspci detects an NVIDIA device
        +
nvidia-smi fails
        |
        v
Possible issue: NVIDIA driver-to-GPU communication failure
```

This is intentionally different from claiming that the GPU is absent or physically defective. A finding contains an evidence chain such as:

```text
Evidence
  source: lspci
  matched: NVIDIA PCI device detected
  detail: The adapter is visible on the PCI bus.

Possible causes
  - NVIDIA driver module issue
  - Driver-GPU communication failure
  - GPU reset failure
  - Hardware instability

Recommendations
  - Review nvidia-smi stderr
  - Check lsmod and dmesg
  - Correlate with Xid and PCIe AER events
```

The output is a troubleshooting direction and an evidence-preserving next step, not an automatic repair action.

## Project structure

```text
gpu-diagnostic/
├── config.yaml
├── scripts/
│   └── gpu-diag.sh
├── src/gpu_diagnostic/
│   ├── analyzer/
│   │   └── rule_engine.py
│   ├── cli/
│   │   └── main.py
│   ├── collector/
│   │   ├── command_runner.py
│   │   ├── driver_collector.py
│   │   ├── gpu_collector.py
│   │   ├── host_collector.py
│   │   ├── log_collector.py
│   │   ├── pci_collector.py
│   │   ├── runtime_collector.py
│   │   └── system_collector.py
│   ├── knowledge/
│   │   └── rules.yaml
│   ├── models/
│   │   ├── finding.py
│   │   ├── report.py
│   │   ├── run.py
│   │   └── snapshot.py
│   ├── reporter/
│   │   ├── html_reporter.py
│   │   └── json_reporter.py
│   ├── services/
│   │   └── diagnostic_service.py
│   └── utils/
│       └── config.py
├── tests/
│   ├── fixtures/
│   ├── test_analyzer.py
│   ├── test_phase2.py
│   └── test_rule_engine.py
├── pyproject.toml
├── setup.py
└── requirements.txt
```

### Module responsibilities

`collector/` contains the system-facing adapters. `CommandRunner` centralizes timeout handling, missing-command handling, permission errors, stdout/stderr capture, and return codes. The individual collectors do not decide root cause.

`models/` contains the data contracts exchanged between layers. `DiagnosticSnapshot` stores collected facts, `Finding` stores an explainable rule result, `DiagnosticRun` stores one complete task, and `DiagnosticReport` remains available as the earlier report model.

`analyzer/` contains rule execution. The current `RuleEngine` uses a deliberately small YAML subset parser so the tool has no third-party runtime dependency on a minimally provisioned support host.

`knowledge/rules.yaml` is the version-controlled rule library. Every rule includes an identifier, name, severity, category, match conditions, description, possible causes, and recommendations.

`reporter/` contains output adapters. JSON is intended for automation and later processing; HTML is a single file for attaching to an incident or opening locally in a browser.

`services/` coordinates the collect → analyze → report workflow.

`cli/` provides the `gpu-diag` command-line interface.

## Requirements and installation

The project requires:

- Python 3.10 or newer.
- A Linux host is the target runtime environment.
- NVIDIA utilities are needed for the corresponding checks: `nvidia-smi`, `lspci`, `lsmod`, `dmesg`, and optionally `nvcc` and PyTorch.

The Python project currently declares no third-party runtime dependencies. Missing Linux commands and unavailable optional tools are recorded in the snapshot instead of terminating the complete diagnostic run.

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On a real Linux NVIDIA server, some commands may require appropriate privileges. The tool preserves permission errors as command evidence; it does not silently elevate privileges or modify the host.

## CLI usage

Show the available commands and options:

```bash
gpu-diag --help
```

Collect a snapshot and write report artifacts without running rule analysis:

```bash
gpu-diag collect
```

Run the complete diagnostic workflow:

```bash
gpu-diag diagnose
```

Provide an expected GPU inventory for a multi-GPU server:

```bash
gpu-diag diagnose --expected-gpus 4
```

Choose an output directory:

```bash
gpu-diag diagnose --output-dir reports/server-01
```

The shell launcher provides the same workflow without requiring package installation first:

```bash
./scripts/gpu-diag.sh diagnose
./scripts/gpu-diag.sh diagnose --expected-gpus 4
```

The current CLI prints a concise summary similar to:

```text
Diagnostic Summary:
Status: WARNING
Findings: 1
Findings:
1. [WARNING] CUDA toolkit compiler unavailable
JSON Report: reports/diagnostic_<run-id>.json
HTML Report: reports/diagnostic_<run-id>.html
```

`PASS` means no rule matched. It does not mean that every possible hardware or software condition has been proven healthy.

## Configuration

The repository root contains [config.yaml](config.yaml):

```yaml
temperature_threshold: 85
expected_gpu_count: null
expected_persistence_mode: null
log_keywords: [NVRM, Xid, PCI, AER]
```

Supported settings:

- `temperature_threshold`: sampled temperature in degrees Celsius used by the high-temperature rule.
- `expected_gpu_count`: optional expected inventory. `null` disables the count comparison unless `--expected-gpus` is supplied.
- `expected_persistence_mode`: optional expected value compared with the value reported by `nvidia-smi`.
- `log_keywords`: keywords used by `LogCollector` when selecting relevant `dmesg` lines.

The configuration loader is intentionally small and supports the format used by the checked-in file. It is not intended to be a general-purpose YAML implementation.

## Reports

Each diagnosis writes two artifacts under the selected output directory:

### JSON

The JSON artifact contains the run identifier, timestamp, hostname, status, finding count, host information, snapshot, collector results, and structured findings. Each finding includes:

- severity and rule identifier;
- title and description;
- evidence source, matched text, and detail;
- possible causes;
- recommendations.

### Static HTML

The HTML artifact contains the same diagnostic context in a browser-readable layout, including host information, status, findings, evidence, possible causes, and recommendations. It is a standalone file generated by `HTMLReporter`; the project does not provide a Flask app, HTTP server, dashboard, or remote report store.

## Testing

Tests use Python's built-in `unittest` framework. The repository currently contains 11 tests and realistic-format log fixtures for Xid 13, Xid 31, Xid 79, CUDA errors, missing GPU evidence, and PCIe/AER errors.

Run the suite from the repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The tests cover:

- structured rule loading;
- keyword and regular-expression matching;
- multi-source PCIe/`nvidia-smi` reasoning;
- Xid and PCIe fixture analysis;
- GPU inventory comparison;
- CUDA and PyTorch findings;
- configuration loading;
- `DiagnosticRun` status calculation;
- static HTML generation and HTML escaping;
- Persistence Mode configuration matching.

The fixtures are log inputs for analyzer regression tests. They are not GPU simulation data and do not claim to represent a particular production server.

## Relationship to GPU-Stress-Lab

GPU Diagnostic Platform complements, rather than duplicates, GPU-Stress-Lab.

GPU-Stress-Lab focuses on applying GPU workloads, observing runtime behavior, and displaying live temperature, utilization, memory, and stress-test information. GPU Diagnostic Platform starts after an abnormal condition is observed: it gathers Linux/NVIDIA evidence, correlates independent signals, and produces a report for troubleshooting.

In a practical workflow:

```text
GPU-Stress-Lab: reproduce or observe an abnormal behavior
        |
        v
GPU Diagnostic Platform: collect evidence and provide investigation directions
```

The diagnostic platform deliberately does not reimplement continuous monitoring or stress testing.

## Design principles

1. Evidence before conclusion.
2. Multiple signals are stronger than a single command result.
3. Possible causes are preferable to absolute hardware claims.
4. Linux and NVIDIA native tools are used as primary evidence sources.
5. Collection, analysis, models, and reporting remain separate layers.
6. Reports are both machine-readable and human-readable.
7. Partial collection is useful: missing commands and permission failures are preserved as evidence.
8. Diagnostic commands should be safe and observational by default.

## Scope and limitations

The current project is intentionally bounded:

- It primarily targets single-host Linux NVIDIA GPU environments.
- PCIe and kernel-driver checks may be incomplete or virtualized under WSL2, containers, or restricted environments.
- It provides investigation directions, possible causes, and recommendations; it does not certify a component as failed.
- It does not automatically reset GPUs, unload drivers, reboot hosts, or change system configuration.
- It has no real-time monitoring loop, Web Dashboard, remote fleet management, distributed diagnosis, AI diagnosis, or cloud service.
- Optional `nvcc` and PyTorch checks depend on what is installed in the current host/Python environment.
- A `PASS` result means no implemented rule matched the collected snapshot, not that every possible failure mode was eliminated.

## Future work

The following are possible future directions and are not implemented in the current release:

- additional NVIDIA Xid and PCIe rule coverage;
- stronger cross-source fault correlation;
- support-bundle export and redaction;
- server verification/baseline mode;
- optional report history management;
- carefully scoped remote diagnostic workflows.

## License

No license file is currently included in the repository. Add a license before publishing if you want to define reuse and contribution terms explicitly.
