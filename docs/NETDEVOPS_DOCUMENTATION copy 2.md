# 📘 NetDevOps Practice Documentation (Engineering Journal)

## 🧭 Purpose

This document serves as the engineering journal for the NetDevOps automation project.

It tracks:

- architecture evolution
- technical decisions
- debugging insights
- automation maturity
- lessons learned
- framework progression

This file is updated only when meaningful architectural or operational improvements occur.

---

# 📌 Project Summary

This project focuses on building a modular NetDevOps automation framework using:

- Python
- Netmiko
- YAML
- Jinja2
- Cisco IOS-XE (DevNet Sandbox)

The project evolved progressively from manual SSH automation into a scalable automation framework featuring:

- interface provisioning
- YAML-driven inventory
- Jinja2 configuration rendering
- compliance validation
- drift detection
- automated remediation
- JSON reporting
- HTML dashboard generation
- idempotent automation logic

---

# 🏗 Architecture Evolution

---

# PHASE 1 — Manual Netmiko Connectivity

## Objective

Establish SSH connectivity to Cisco IOS-XE devices using Netmiko.

## Features Implemented

- SSH authentication
- show command execution
- send_config_set()

## Example

```python
conn = ConnectHandler(**device)

output = conn.send_command("show ip interface brief")
```

## Lessons Learned

- Netmiko automatically enters/exits config mode
- Cisco IOS-XE command sequencing matters
- Interface modes affect IP assignment behavior

---

# PHASE 2 — Semi-Automated Interface Provisioning

## Objective

Automate interface configuration using Python dictionaries.

## Features Implemented

- Multi-interface provisioning
- Layer-2 and Layer-3 support
- Routed interface automation
- Validation engine
- Rollback logic
- Local backups

## Initial Desired State Model

```python
desired_config = {
    "GigabitEthernet1/0/2": {
        "description": "LAB1",
        "ip": "10.20.30.1",
        "mask": "255.255.255.0"
    }
}
```

## Key Learning

### Layer-2 vs Layer-3 Interfaces

Issue:

```bash
% Invalid input detected
```

Cause:
Interface was operating as a Layer-2 switchport.

Fix:

```bash
no switchport
```

before applying:

```bash
ip address X.X.X.X X.X.X.X
```

---

# PHASE 3 — Compliance & Drift Detection Engine

## Objective

Introduce validation-first automation logic.

## Features Implemented

- Desired state comparison
- Drift detection
- Compliance engine
- Remediation engine
- JSON reporting
- HTML reporting

## Automation Workflow

```text
Connect
   ↓
Collect Running Config
   ↓
Compare Desired vs Actual
   ↓
Compliance Validation
   ↓
Drift Detection
   ↓
Remediation
   ↓
Reporting
```

---

# PHASE 4 — YAML-Driven Inventory

## Objective

Separate configuration data from application logic.

## Features Implemented

- inventory/devices.yml
- inventory/interfaces.yml
- load_inventory.py
- .env credential injection
- Multi-device ready architecture

## Example Device Inventory

```yaml
devices:
  - device_type: cisco_xe
    host: devnetsandboxiosxec9k.cisco.com
```

## Example Interface Inventory

```yaml
interfaces:
  - interface: GigabitEthernet1/0/2
    description: YAML LAB1
    routed: true
    ip: 10.10.10.1
    mask: 255.255.255.0
    enabled: true
```

## Key Learning — Reusable Module vs Script Design

**Problem with original load_inventory.py:**

Code ran at module level — executed immediately on import.
`print(devices)` side effect polluted any script that imported it.

**Fix:**

Refactored into two clean reusable functions:

```python
def load_devices(filepath="inventory/devices.yml"):
    ...
    return devices

def load_interfaces(filepath="inventory/interfaces.yml"):
    ...
    return data["interfaces"]
```

No code runs on import. Only executes when the function is explicitly called.
Now safely reusable across any script in the framework.

## Benefits

- cleaner architecture
- reusable automation
- scalable inventory model
- secure credential handling

---

# PHASE 5 — Jinja2 Templating

## Objective

Move from hardcoded CLI generation to dynamic templates.

## Features Implemented

- templates/interface.j2
- Dynamic configuration rendering
- YAML + Jinja2 integration
- Template-driven deployments

## Jinja2 Workflow

```text
YAML Inventory
      ↓
load_inventory.py
      ↓
Jinja2 Template Engine
      ↓
Rendered Config
      ↓
Netmiko Deployment
```

## Example Template

```jinja2
interface {{ interface }}
 description {{ description }}
{% if routed %}
 no switchport
 ip address {{ ip }} {{ mask }}
{% else %}
 switchport
{% endif %}
{% if enabled %}
 no shutdown
{% else %}
 shutdown
{% endif %}
```

## Key Learning — Template Indentation

Cisco IOS-XE requires interface sub-commands to be indented with a leading space.
Templates must include the space before each sub-command or some IOS versions
will reject or misparse the commands.

Blank lines between commands must also be stripped before sending via Netmiko
to avoid pushing empty commands to the device.

---

# PHASE 6 — FULL_CONSOLIDATED_NETDEVOPS_SCRIPT_V3

## Objective

Build a modular, idempotent, production-style NetDevOps workflow.

## Full Architecture

```text
.env (credentials)
        ↓
load_inventory.py
  ├── load_devices()     → inventory/devices.yml
  └── load_interfaces()  → inventory/interfaces.yml
        ↓
Backup Running Config   → backups/
        ↓
Extract Interface Blocks
        ↓
Subset Compliance Check
        ↓
Remediate on DRIFT only
        ↓
JSON + HTML Reports     → reports/
```

## Major Improvements Over V2

---

### Fix 1 — Desired State No Longer Hardcoded

V2 hardcoded desired state in Python:

```python
desired_config = {
    "GigabitEthernet1/0/2": { "description": "LAB1", ... }
}
```

V3 loads it from YAML:

```python
interfaces = load_interfaces()
```

Change desired state by editing `interfaces.yml` only. No Python changes needed.

---

### Fix 2 — Diff Engine Rebuilt (Interface Block Extraction)

**Problem in V2:**

Compared expected lines against the entire running config (thousands of lines).
Always returned DRIFT even after correct remediation — false positives on every run.

**Fix in V3:**

Added `extract_interface_block()` to pull only the relevant section:

```python
def extract_interface_block(running_config, interface_name):
    # Finds the interface block and returns only its sub-commands
    # Normalizes whitespace on both sides before comparison
```

---

### Fix 3 — Subset Compliance Check (Not Exact Match)

**Problem:**

Cisco IOS automatically adds default lines to interface blocks:
- `negotiation auto`
- `spanning-tree portfast`
- and others not under our control

An exact diff flagged these as DRIFT even when our config was perfectly applied.

**Fix:**

Switched from exact diff to subset check:

```python
missing = [
    line for line in expected
    if line not in actual
]
```

COMPLIANT = all expected lines present in actual block.
DRIFT = one or more expected lines missing.
Extra Cisco default lines are ignored.

---

### Fix 4 — `no shutdown` Is Invisible in Running Config

**Problem:**

`no shutdown` was included in expected lines.
Cisco IOS never writes `no shutdown` to running config — it is the default state and invisible.
This caused permanent false DRIFT on all enabled interfaces regardless of actual device state.

**Fix:**

Removed `no shutdown` from expected lines entirely.
Only `shutdown` is checked, and only when `enabled: false`.

---

### Fix 5 — Remediation Pushes Full Desired Config

**V2 remediation (incomplete):**

```python
cfg = [f"interface {intf}", "no shutdown"]
```

Only brought the interface up. Never fixed description, IP, or mode.

**V3 remediation (complete):**

Pushes the full desired config for every DRIFT interface:
- description
- routed/switchport mode
- ip address and mask
- shutdown state

---

## Idempotency — Proven in Practice

After all V3 fixes, two consecutive runs confirmed correct behavior:

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

📄 [View Drift Dashboard — Run 1](images/screenshoots/DRIFT_DASHBOARD_V3.png)

---

### Run 2 — Idempotency Confirmed (No Remediation Triggered)

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

📄 [View Compliant Dashboard — Run 2](images/screenshoots/COMPLIANT_DASHBOARD_V3.png)

The framework only acts when action is needed.
This is the gold standard for production automation.

---

# PHASE 7 — Structured Logging (V4)

## Objective

Add production-grade operational visibility and audit trail.

## Features Implemented

- `scripts/logger.py` — reusable logging module
- Simultaneous console and file logging
- `logs/netdevops.log` — persistent execution audit trail
- Log levels: INFO, WARNING, ERROR
- Windows UTF-8 encoding fix for PowerShell compatibility
- Error handling with try/except on connect, backup, and reports

## Logger Module Design

```python
def get_logger(name="netdevops"):
    # Console handler — live output during execution
    # File handler   — persistent audit log
    # Format: 2026-05-18 09:12:41 | INFO     | message
```

Importable by any script in the framework:

```python
from logger import get_logger
log = get_logger()
```

## Log Level Mapping

| Event | Level |
|---|---|
| Connecting, backup saved, reports generated | INFO |
| Drift detected, remediating interface | WARNING |
| Connection failed, backup failed, report failed | ERROR |

## Key Learning — Windows UTF-8 Encoding

**Problem:**

PowerShell defaults to `cp1252` encoding.
Unicode characters like `→` caused `UnicodeEncodeError` on the console handler.

**Fix in logger.py:**

```python
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
```

Also applied `encoding="utf-8"` to the file handler explicitly.

## Example Log Output

```bash
2026-05-18 22:30:27 | INFO     | NetDevOps Framework V4 — Execution Started
2026-05-18 22:30:29 | INFO     | Connection established — devnetsandboxiosxec9k.cisco.com
2026-05-18 22:30:30 | INFO     | Backup saved — backups/backup_xxx.txt
2026-05-18 22:30:30 | WARNING  | [DRIFT] GigabitEthernet1/0/2 → DRIFT
2026-05-18 22:30:30 | INFO     | Remediation successful — GigabitEthernet1/0/2
2026-05-18 22:30:30 | INFO     | All interfaces COMPLIANT — no remediation needed
```

---

# PHASE 8 — Rendered Config Archival (V5)

## Objective

Save Jinja2-rendered configs to disk before deployment for
archival, review, and dry-run foundation.

## Features Implemented

- `configs/generated/` directory — auto-created at runtime
- `render_and_save_configs()` — new function in V5
- Rendered config saved per device per run with metadata header
- Config file path logged and included in JSON + HTML reports

## Updated Pipeline

```text
.env (credentials)
        ↓
load_inventory.py
        ↓
Backup Running Config     → backups/
        ↓
Render via Jinja2         → configs/generated/   ← NEW
        ↓
Extract Interface Blocks
        ↓
Subset Compliance Check
        ↓
Remediate on DRIFT only
        ↓
JSON + HTML Reports       → reports/
```

## Rendered Config File Format

```text
! Generated by NetDevOps Framework V5
! Device    : devnetsandboxiosxec9k.cisco.com
! Timestamp : 20260519_090000
!
interface GigabitEthernet1/0/2
 description YAML LAB1
 no switchport
 ip address 10.10.10.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet1/0/3
 description YAML LAB2
 switchport
 shutdown
!
```

## Benefits

- human-readable record of intended changes
- dry-run foundation — review before pushing
- rollback reference — know exactly what was deployed
- config archival trail — timestamped per run

---

# PHASE 9 — Dry-Run Mode (V6)

## Objective

Add safe execution mode that validates and reports
without pushing any changes to the device.

## Features Implemented

- `argparse` — CLI argument parsing
- `--dry-run` flag
- `EXECUTION_MODE` — `DRY-RUN` or `LIVE`
- Mode stamped in logs, HTML report, JSON report, and rendered config file
- Remediation fully skipped in dry-run mode
- All other steps (backup, render, diff, compliance, reports) still execute

## Usage

```bash
# Validate only — no changes pushed
python scripts/FULL_CONSOLIDATED_NETDEVOPS_SCRIPT_V6.py --dry-run

# Full live execution
python scripts/FULL_CONSOLIDATED_NETDEVOPS_SCRIPT_V6.py
```

## Dry-Run Pipeline Behavior

| Step | DRY-RUN | LIVE |
|---|---|---|
| Connect | ✅ | ✅ |
| Backup | ✅ | ✅ |
| Render configs | ✅ | ✅ |
| Diff engine | ✅ | ✅ |
| Compliance check | ✅ | ✅ |
| Remediation | ❌ skipped | ✅ |
| Reports | ✅ | ✅ |

## Example Dry-Run Output

```bash
2026-05-21 05:38:36 | INFO     | NetDevOps Framework V6 — DRY-RUN MODE
2026-05-21 05:38:38 | INFO     | [OK]    GigabitEthernet1/0/2 → COMPLIANT
2026-05-21 05:38:38 | INFO     | [OK]    GigabitEthernet1/0/3 → COMPLIANT
2026-05-21 05:38:38 | INFO     | [OK]    GigabitEthernet1/0/4 → COMPLIANT
2026-05-21 05:38:38 | WARNING  | DRY-RUN MODE — remediation skipped, no changes pushed
2026-05-21 05:38:38 | INFO     | HTML report saved — reports/html/report_20260521_053836.html
```

📄 [View Dry-Run Dashboard](images/screenshoots/Screenshot 2026-05-21 115924_DRY_RUN_V6.png)

---

# 📊 Current Capabilities

## Successfully Implemented

- Multi-interface automation
- YAML inventory loading
- Jinja2 templating
- Drift detection
- Compliance validation
- Automated remediation (full config push)
- Structured logging (console + file)
- Rendered config archival (`configs/generated/`)
- Dry-run mode (`--dry-run` flag)
- HTML dashboard generation
- JSON structured reporting
- Local backup generation
- Idempotent re-runs (proven)
- Modular architecture
- GitHub Actions CI/CD pipeline

---

# 📁 Current Project Structure

```text
python-netmiko-devnet-cisco/
│
├── backups/
├── configs/
│   └── generated/
├── docs/
├── inventory/
│   ├── devices.yml
│   └── interfaces.yml
├── logs/
│   └── netdevops.log
├── reports/
│   ├── html/
│   └── json/
├── scripts/
│   ├── cisco_connect.py
│   ├── send_multi_command.py
│   ├── send_config_set.py
│   ├── multi_interfaces_validation_rollback.py
│   ├── load_inventory.py
│   ├── logger.py
│   ├── yaml_jinja2_netmiko.py
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

# 🔐 Operational Principles

This project follows core NetDevOps engineering principles:

- backup before change
- validate after deployment
- automate remediation safely
- maintain idempotency
- separate logic from data
- prefer declarative models
- reusable modules over duplicate scripts
- observe before you act (logging first)
- review before you push (dry-run before live)

---

# 🚧 Current Limitations

- Single vendor focus (Cisco IOS-XE)
- No RESTCONF/API integration yet
- No database-backed inventory yet
- No scheduled compliance jobs yet
- `tests/` directory empty — no automated test coverage yet
- Monolithic script architecture — modularization into `core/` pending

---

# 🚀 Planned Roadmap

## Short-Term

- Modularization into `scripts/core/` (next)
- Logging improvements (rotating logs, execution IDs, per-device logs)
- YAML schema validation

## Mid-Term

- Multi-device orchestration testing
- RESTCONF integration
- PyATS/Genie validation
- CSV/Excel inventory support

## Long-Term

- Intent-based networking
- Flask/FastAPI dashboard
- Real-time compliance engine
- Multi-vendor support

---

# ✍️ Maintainer

Cyprien Carlos Temateu
NetDevOps / Network Automation Practice Lab