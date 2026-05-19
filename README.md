# 📘 🚀 NetDevOps Automation Framework

Production-style Cisco IOS-XE network automation using Python, Netmiko, YAML inventory, Jinja2 templating, compliance validation, drift detection, remediation, and reporting.

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

---

## 🏗 Architecture

```text
.env (credentials)
        ↓
load_inventory.py
  ├── load_devices()     → inventory/devices.yml
  └── load_interfaces()  → inventory/interfaces.yml
        ↓
Jinja2 Template Engine  → templates/interface.j2
        ↓
Netmiko SSH Connection
        ↓
Backup Running Config
        ↓
Extract Interface Blocks
        ↓
Subset Compliance Check
        ↓
Remediate on DRIFT only
        ↓
JSON + HTML Reports
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
├── backups/
├── configs/
├── docs/
├── inventory/
│   ├── devices.yml
│   └── interfaces.yml
├── reports/
│   ├── html/
│   └── json/
├── scripts/
│   ├── cisco_connect.py
│   ├── send_multi_command.py
│   ├── send_config_set.py
│   ├── multi_interfaces_validation_rollback.py
│   ├── load_inventory.py
│   ├── yaml_jinja2_netmiko.py
│   └── FULL_CONSOLIDATED_NETDEVOPS_SCRIPT_V3.py
├── templates/
│   └── interface.j2
├── tests/
├── .github/workflows/
│   └── netdevops-ci.yml
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

### Run 1 — Drift Detected and Remediated

```bash
Connecting to devnetsandboxiosxec9k.cisco.com...
Collecting running config...
Backup saved: backups/backup_devnetsandboxiosxec9k.cisco.com_20260518_081527.txt
Running diff engine...
Running compliance check...
  [DRIFT] GigabitEthernet1/0/2 → DRIFT
  [DRIFT] GigabitEthernet1/0/3 → DRIFT
  [DRIFT] GigabitEthernet1/0/4 → DRIFT
Running remediation...
[REMEDIATED] GigabitEthernet1/0/2 ✔
[REMEDIATED] GigabitEthernet1/0/3 ✔
[REMEDIATED] GigabitEthernet1/0/4 ✔
✔ DONE — devnetsandboxiosxec9k.cisco.com
```

📄 [View Drift Dashboard — Run 1](reports/html/report_20260518_081527.html)

---

### Run 2 — Idempotency Confirmed (No Remediation)

```bash
Connecting to devnetsandboxiosxec9k.cisco.com...
Collecting running config...
Backup saved: backups/backup_devnetsandboxiosxec9k.cisco.com_20260518_082738.txt
Running diff engine...
Running compliance check...
  [OK] GigabitEthernet1/0/2 → COMPLIANT
  [OK] GigabitEthernet1/0/3 → COMPLIANT
  [OK] GigabitEthernet1/0/4 → COMPLIANT
Running remediation...
✔ DONE — devnetsandboxiosxec9k.cisco.com
```

📄 [View Compliant Dashboard — Run 2](reports/html/report_20260518_082738.html)

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

- Logging framework (loguru / logging module)
- REST API integration
- Scheduled compliance audits
- Intent-based networking
- Multi-device orchestration
- API dashboard

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