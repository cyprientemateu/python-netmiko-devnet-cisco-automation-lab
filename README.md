# 📘 🚀 NetDevOps Automation Framework

Production-style Cisco IOS-XE network automation using Python, Netmiko, YAML inventory, Jinja2 templating, compliance validation, drift detection, remediation, structured logging, config archival, and dry-run mode.

## 🧭 Project Overview

This project demonstrates real-world NetDevOps automation practices using Python and Netmiko against Cisco IOS-XE devices (DevNet Sandbox).

It has evolved from simple SSH command execution into a full data-driven automation framework including:

- YAML-driven device and interface inventory
- Jinja2 configuration templating
- Interface provisioning
- Multi-interface automation
- Validation engine
- Drift detection
- Automatic remediation
- Structured logging with audit trail
- Rendered config archival before deployment
- Dry-run mode for safe validation
- Backup system
- JSON + HTML reporting dashboard

---

## 🚀 Key Features

### ✅ Network Automation
- Configure multiple interfaces
- Support Layer-2 and Layer-3 modes
- Assign IP addresses automatically
- Enable/disable interfaces
- Jinja2-templated config generation
- YAML inventory-driven execution

### ✅ Safety & Reliability
- Pre-change configuration backup
- Post-change validation
- Automatic rollback support
- Idempotent execution (safe re-runs, proven)

### ✅ Compliance Engine
- Desired state loaded from YAML (not hardcoded)
- Interface block extraction from running config
- Subset-based compliance check (avoids false positives)
- Drift detection and classification

### ✅ Reporting System
- JSON structured reports
- HTML dashboard reports
- Timestamped outputs
- Execution mode stamped in every report

### ✅ Observability
- Structured logging via Python `logging` module
- Simultaneous console and file output
- Persistent audit trail in `logs/netdevops.log`
- INFO / WARNING / ERROR log levels

### ✅ Config Archival & Dry-Run
- Jinja2-rendered configs saved to `configs/generated/` before deployment
- `--dry-run` flag — validate and report without pushing changes
- Execution mode (DRY-RUN / LIVE) visible in logs and reports

---

## 🏗 Architecture

```text
.env (credentials)
        ↓
load_inventory.py
  ├── load_devices()     → inventory/devices.yml
  └── load_interfaces()  → inventory/interfaces.yml
        ↓
Backup Running Config     → backups/
        ↓
Render via Jinja2         → configs/generated/
        ↓
Extract Interface Blocks
        ↓
Subset Compliance Check
        ↓
Remediate on DRIFT only   ← skipped in --dry-run
        ↓
JSON + HTML Reports       → reports/
        ↓
Structured Logging        → logs/netdevops.log
```

---

## 🧰 Technologies Used

- Python 3.11
- Netmiko
- Cisco IOS-XE (DevNet Sandbox)
- Jinja2
- PyYAML
- python-dotenv
- TextFSM
- HTML + JSON reporting
- GitHub Actions (CI/CD)
- PowerShell

---

## 📁 Project Structure

```text
python-netmiko-devnet-cisco/
│
├── archive/
│   ├── README.md
│   └── legacy_scripts/
│       ├── cisco_connect.py
│       ├── send_multi_command.py
│       ├── send_config_set.py
│       ├── multi_interfaces_validation_rollback.py
│       ├── multi_interfaces_validation_rollback_backup_device_local.py
│       ├── jinja2_interface_generator.py
│       ├── load_inventory_V1.py
│       ├── FULL_CONSOLIDATED_NETDEVOPS_SCRIPT.py
│       ├── FULL_CONSOLIDATED_NETDEVOPS_SCRIPT_V2.py
│       └── NETDEVOPS_DOCUMENTATION_V1.md
├── backups/
├── configs/
│   └── generated/
├── docs/
│   ├── NETDEVOPS_DOCUMENTATION.md
│   └── python_and_network_automation.docx
├── images/
│   └── screenshoots/
├── inventory/
│   ├── devices.yml
│   └── interfaces.yml
├── logs/
│   └── netdevops.log
├── reports/
│   ├── html/
│   └── json/
├── scripts/
│   ├── load_inventory.py
│   ├── logger.py
│   ├── yaml_jinja2_netmiko_deployer.py
│   ├── FULL_CONSOLIDATED_NETDEVOPS_SCRIPT_V3.py
│   ├── FULL_CONSOLIDATED_NETDEVOPS_SCRIPT_V4.py
│   ├── FULL_CONSOLIDATED_NETDEVOPS_SCRIPT_V5.py
│   └── FULL_CONSOLIDATED_NETDEVOPS_SCRIPT_V6.py
├── templates/
│   └── interface.j2
├── tests/
├── .github/
│   └── workflows/
│       └── netdevops-ci.yml
│
├── README.md
├── requirements.txt
├── .env
├── .gitignore
└── LICENSE
```

---

## ⚙️ How It Works

### 1️⃣ Inventory Loading
- `load_devices()` reads `inventory/devices.yml`
- `load_interfaces()` reads `inventory/interfaces.yml`
- Credentials injected from `.env` at runtime

### 2️⃣ Backup Phase
- Captures running configuration via `show running-config`
- Stores timestamped backup in `/backups`

### 3️⃣ Diff Engine
- Extracts per-interface config blocks from running config
- Compares against desired state using subset logic
- Avoids false positives from Cisco-generated default lines

### 4️⃣ Compliance Engine
- Classifies each interface as:
    - COMPLIANT
    - DRIFT

### 5️⃣ Remediation
- Triggered only when DRIFT is detected
- Pushes full desired config (description, IP, mode, state)
- Skips interfaces already COMPLIANT (idempotent)

### 6️⃣ Reporting
- Generates:
    - JSON report (machine-readable)
    - HTML dashboard (visual report)

---

## ✅ Current Capabilities

- YAML-driven device and interface inventory
- Reusable inventory loader module
- Jinja2 configuration templating
- Multi-interface configuration
- Routed (L3) and switched (L2) interface support
- Drift detection
- Compliance validation
- Automated remediation (full config push)
- Structured logging (console + file audit trail)
- Rendered config archival (`configs/generated/`)
- Dry-run mode (`--dry-run` flag)
- Backup generation
- HTML reporting dashboard
- JSON reporting
- Idempotent execution (proven)
- GitHub CI pipeline integration

---

## ⚙️ Key Concepts Learned

### Layer-2 vs Layer-3 Interfaces

Issue:
```bash
% Invalid input detected
```
Fix:
```bash
no switchport
ip address X.X.X.X X.X.X.X
```

### Diff Engine — Subset Check vs Exact Match

Issue:
- Exact diff comparison always returned DRIFT even after correct remediation
- Cisco IOS adds default lines (`negotiation auto`, `spanning-tree`, etc.)
- `no shutdown` is never written to running-config (it is the default)

Fix:
- Extract only the relevant interface block from running config
- Use subset check: verify all expected lines are present, ignore extras
- Exclude `no shutdown` from expected lines

---

## 📊 Example Output

### Dry-Run — Validate Only (No Changes Pushed)

```bash
2026-05-21 05:38:36 | INFO     | NetDevOps Framework V6 — DRY-RUN MODE
2026-05-21 05:38:38 | INFO     | [OK]    GigabitEthernet1/0/2 → COMPLIANT
2026-05-21 05:38:38 | INFO     | [OK]    GigabitEthernet1/0/3 → COMPLIANT
2026-05-21 05:38:38 | INFO     | [OK]    GigabitEthernet1/0/4 → COMPLIANT
2026-05-21 05:38:38 | WARNING  | DRY-RUN MODE — remediation skipped, no changes pushed
```

📄 [View Dry-Run Dashboard](images/screenshoots/Screenshot 2026-05-21 115924_DRY_RUN_V6)

---

### Run 1 — Drift Detected and Remediated

```bash
2026-05-18 22:22:30 | WARNING  | [DRIFT] GigabitEthernet1/0/2 → DRIFT
2026-05-18 22:22:30 | WARNING  | [DRIFT] GigabitEthernet1/0/3 → DRIFT
2026-05-18 22:22:30 | WARNING  | [DRIFT] GigabitEthernet1/0/4 → DRIFT
2026-05-18 22:22:33 | INFO     | Remediation successful — GigabitEthernet1/0/2
2026-05-18 22:22:34 | INFO     | Remediation successful — GigabitEthernet1/0/3
2026-05-18 22:22:35 | INFO     | Remediation successful — GigabitEthernet1/0/4
```

📄 [View Drift Dashboard — Run 1](images/screenshoots/DRIFT_DASHBOARD_V3.png)

---

### Run 2 — Idempotency Confirmed (No Remediation)

```bash
2026-05-18 22:30:30 | INFO     | [OK]    GigabitEthernet1/0/2 → COMPLIANT
2026-05-18 22:30:30 | INFO     | [OK]    GigabitEthernet1/0/3 → COMPLIANT
2026-05-18 22:30:30 | INFO     | [OK]    GigabitEthernet1/0/4 → COMPLIANT
2026-05-18 22:30:30 | INFO     | All interfaces COMPLIANT — no remediation needed
```

📄 [View Compliant Dashboard — Run 2](images/screenshoots/COMPLIANT_DASHBOARD_V3)

---

## 🔐 Best Practices Used

- Always backup before changes
- Validate after configuration
- Avoid manual verification
- Ensure idempotent automation
- Use structured reporting
- Externalize inventory and credentials
- Separate concerns (inventory, templating, execution)

---

## 🚀 Future Improvements

- Modularization into `scripts/core/` (next)
- Logging improvements (rotating logs, execution IDs, per-device logs)
- YAML schema validation
- Multi-device orchestration
- RESTCONF integration
- PyATS/Genie validation
- Flask/FastAPI dashboard
- Intent-based networking

---

## 🧪 Learning Outcome

This project demonstrates:

- Real-world network automation design
- Infrastructure as Code thinking
- Validation-first engineering approach
- Data-driven automation (YAML + Jinja2)
- Scalable automation architecture
- Idempotent execution model

---

## ✍️ Maintainer
Cyprien Carlos Temateu
NetDevOps Practice Lab