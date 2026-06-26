# azure_support_engineer_p0
# SRE Diagnostic & Automated VM Deployment Tool

A Python-based command-line tool that runs local system diagnostics and automates Azure VM provisioning — built as part of an SRE training program.

---

## Overview

This tool gives an engineer two capabilities from a single interactive menu:

1. **Local Diagnostics** — collects CPU, memory, disk, and network stats from the host machine, formats them into a readable report, and appends results to a persistent history file.
2. **Azure VM Deployment** — authenticates via the Azure CLI and provisions a free-tier virtual machine with auto-shutdown and a teardown routine to prevent cost overruns.

---

## Technologies

| Tool | Purpose |
|---|---|
| Python 3 | Core application logic and subprocess orchestration |
| Bash / Linux CLI | `ps`, `free`, `df`, `ss` — system diagnostics |
| Azure CLI (`az`) | Authentication and cloud resource provisioning |
| Git | Version control |

---

## Project Structure

```
azure_support_engineer_p0/
├── main.py                  # Entry point — interactive CLI menu
├── diagnostics.py           # Local system diagnostics module
├── azure_deploy.py          # Azure VM provisioning module
├── history.py               # Persistent performance history (JSON)
├── performance_history.json # Auto-generated on first diagnostic run
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- Azure CLI installed and available on your PATH
- A Linux or macOS environment (WSL works on Windows)

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/azure_support_engineer_p0.git
cd azure_support_engineer_p0
```

### Running the Tool

```bash
python main.py
```

---

## Features

### 1. Interactive CLI Menu

Navigate all tool functions without typing command-line flags.

```
=============================
  SRE Diagnostic Tool v1.0
=============================
1. Run Local Diagnostics
2. Deploy Azure VM
3. Run Teardown
4. View Performance History
5. Exit

Select an option:
```

### 2. Local System Diagnostics

Collects and formats the following metrics from the host machine:

- **CPU usage** — via `ps`
- **Memory utilization** — via `free`
- **Disk usage** — via `df`
- **Active network connections** — via `ss`

Output is printed as a formatted summary report and saved to `performance_history.json`.

### 3. Automated Azure VM Deployment

Provisions a cloud VM through the Azure CLI with the following sequence:

1. Check authentication status (`az account show`)
2. Authenticate if needed (`az login`)
3. Create a resource group
4. Deploy a `Standard_B1s` VM with Standard HDD storage
5. Configure auto-shutdown at 18:00 local time
6. Confirm provisioning state (`az vm show`)

### 4. Teardown Routine

Destroys all provisioned Azure resources to prevent residual charges:

```bash
az group delete --name <resource-group> --yes --no-wait
```

Run this at the end of every session.

### 5. Persistent Performance History

Every diagnostic run appends results to `performance_history.json` with a timestamp. View the full history from within the menu.

```json
[
  {
    "timestamp": "2025-07-01T10:30:00",
    "metrics": {
      "cpu": "23%",
      "memory_used": "1.2GB",
      "disk_used": "45%",
      "active_connections": "12"
    }
  }
]
```

---

## Zero-Cost / Free-Tier Constraints

All Azure deployments are strictly configured to avoid charges:

| Constraint | Value |
|---|---|
| VM Size | `Standard_B1s` only |
| Storage | Standard HDD (no Premium SSD) |
| Auto-Shutdown | Daily at 18:00 local time |
| Teardown | `az group delete` required after each session |

> **Warning:** Always run the teardown routine when finished. Leaving a VM running will consume Azure free credits.

---

## Extension Features

- [x] Interactive CLI Menu
- [x] Persistent Performance History (local JSON)
- [ ] Azure Blob Storage for remote history
- [ ] Slack/Discord webhook notifications on deploy success/failure

---

## Author

Bryan — SRE Training Cohort, 2406