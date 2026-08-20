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
- YAML schema validation (Pydantic)
- Jinja2 configuration rendering
- compliance validation (Netmiko CLI + RESTCONF API)
- drift detection
- automated remediation
- structured logging (rotating, execution IDs, per-device)
- rendered config archival
- dry-run mode
- modular `core/` architecture
- sequential and parallel multi-device orchestration
- RESTCONF API integration (dual-layer validation)
- Flask compliance dashboard (web UI)
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

📄 [View Drift Dashboard — Run 1](../images/screenshoots/DRIFT_DASHBOARD_V3.png)

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

📄 [View Compliant Dashboard — Run 2](../images/screenshoots/COMPLIANT_DASHBOARD_V3.png)

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

📄 [View Dry-Run Dashboard](../images/screenshoots/Screenshot_2026-05-21_115924_DRY_RUN_V6.png)

---

# PHASE 10 — Modular Core Architecture (main.py)

## Objective

Refactor the monolithic V6 script into a fully modular,
single-responsibility architecture using a `core/` package
and a clean `main.py` orchestrator.

## Features Implemented

- `scripts/core/` package with 6 focused modules
- `scripts/main.py` — pipeline orchestrator only
- All business logic moved out of main script
- Each module independently testable
- `dry_run` passed as explicit parameter — no global state
- All V3–V6 scripts moved to `archive/legacy_scripts/`

## Module Breakdown

| Module | Responsibility |
|---|---|
| `core/connection.py` | SSH connect, get running config |
| `core/backup.py` | Save timestamped backup to disk |
| `core/rendering.py` | Jinja2 rendering, save to configs/generated/ |
| `core/compliance.py` | Build expected lines, extract interface block, diff, compliance check |
| `core/remediation.py` | Push full desired config on DRIFT, dry-run aware |
| `core/reporting.py` | Save JSON report, generate HTML dashboard |

## main.py — Clean Orchestrator

```python
from core.connection  import connect, get_running_config
from core.backup      import save_backup
from core.rendering   import render_and_save_configs
from core.compliance  import diff_configs, compliance_check
from core.remediation import remediate
from core.reporting   import save_json_report, generate_html_report
```

`main.py` contains zero business logic.
It only orchestrates the pipeline and handles the device loop.

## Updated Pipeline

```text
.env (credentials)
        ↓
load_inventory.py
  ├── load_devices()     → inventory/devices.yml
  └── load_interfaces()  → inventory/interfaces.yml
        ↓
core/connection.py        → SSH connect
        ↓
core/backup.py            → backups/
        ↓
core/rendering.py         → configs/generated/
        ↓
core/compliance.py        → diff + compliance check
        ↓
core/remediation.py       → remediate DRIFT (skipped in dry-run)
        ↓
core/reporting.py         → reports/json/ + reports/html/
        ↓
logs/netdevops.log        → audit trail
```

## Proven in Practice

Both modes confirmed working after modularization:

### Dry-Run

```bash
2026-05-21 21:37:48 | INFO     | NetDevOps Framework — DRY-RUN MODE
2026-05-21 21:37:50 | INFO     | [OK]    GigabitEthernet1/0/2 → COMPLIANT
2026-05-21 21:37:50 | INFO     | [OK]    GigabitEthernet1/0/3 → COMPLIANT
2026-05-21 21:37:50 | INFO     | [OK]    GigabitEthernet1/0/4 → COMPLIANT
2026-05-21 21:37:50 | WARNING  | DRY-RUN MODE — remediation skipped, no changes pushed
2026-05-21 21:37:50 | INFO     | NetDevOps Framework — Execution Complete
```

### Live

```bash
2026-05-21 21:37:59 | INFO     | NetDevOps Framework — LIVE MODE
2026-05-21 21:38:02 | INFO     | [OK]    GigabitEthernet1/0/2 → COMPLIANT
2026-05-21 21:38:02 | INFO     | [OK]    GigabitEthernet1/0/3 → COMPLIANT
2026-05-21 21:38:02 | INFO     | [OK]    GigabitEthernet1/0/4 → COMPLIANT
2026-05-21 21:38:02 | INFO     | All interfaces COMPLIANT — no remediation needed
2026-05-21 21:38:02 | INFO     | NetDevOps Framework — Execution Complete
```

## How to Run

```bash
# Validate only
python scripts/main.py --dry-run

# Full live execution
python scripts/main.py
```

## Key Engineering Principle Applied

> A script does one thing from top to bottom.
> A framework has modules with single responsibilities
> that are orchestrated by a clean entry point.

This transition marks the point where the project moved
from automation scripting to production software engineering.

---

# PHASE 11 — Logging Improvements

## Objective

Upgrade the logging system from a basic file logger to a
production-grade observability layer with rotation,
traceability, and per-device isolation.

## Features Implemented

- `RotatingFileHandler` — 5MB max per file, 5 rotated backups
- Execution ID — unique `EXEC-YYYYMMDD-HHMMSS` per run
- `ExecutionIDFilter` — injects ID into every log record
- Per-device log file — `logs/{device_host}.log`
- `add_device_handler()` / `remove_device_handler()` — opens and closes per-device handler cleanly around each device loop

## Log Structure

```
logs/
├── netdevops.log           ← all devices, all runs (rotating)
├── netdevops.log.1         ← previous rotation
└── devnetsandboxiosxec9k.cisco.com.log  ← this device only
```

## Log Format

```
2026-05-26 18:12:17 | INFO     | [EXEC-20260526-181217] | message
```

Every line is traceable to a specific run via the execution ID.

## Key Learning — Singleton Logger Pattern

Core modules call `get_logger()` at import time without an execution ID.
When `main.py` later calls `get_logger(execution_id=exec_id)`, the filter
on the existing singleton is updated — all modules immediately pick up
the new execution ID without reinitialization.

## Example Output

```bash
2026-05-26 18:12:17 | INFO     | [EXEC-20260526-181217] | NetDevOps Framework — LIVE MODE
2026-05-26 18:12:17 | INFO     | [EXEC-20260526-181217] | Execution ID: EXEC-20260526-181217
2026-05-26 18:12:19 | WARNING  | [EXEC-20260526-181217] | [DRIFT] GigabitEthernet1/0/2 → DRIFT
2026-05-26 18:12:20 | INFO     | [EXEC-20260526-181217] | Remediation successful — GigabitEthernet1/0/2
2026-05-26 18:12:23 | INFO     | [EXEC-20260526-181217] | NetDevOps Framework — Execution Complete
```

---

# PHASE 12 — YAML Schema Validation

## Objective

Validate all inventory data against strict Pydantic models
before any SSH connection is made.
Prevent bad config from ever reaching a device.

## Features Implemented

- `scripts/core/validator.py` — new module
- `DeviceModel` — validates device inventory fields
- `InterfaceModel` — validates interface inventory fields
- `validate_inventory()` — collects ALL errors before returning
- Called in `main.py` immediately after loading inventory

## Validation Rules

### DeviceModel

| Field | Rule |
|---|---|
| `host` | Required |
| `device_type` | Required |
| `username` | Must be present — catches missing `.env` |
| `password` | Must be present — catches missing `.env` |

### InterfaceModel

| Field | Rule |
|---|---|
| `interface` | Required |
| `description` | Required |
| `ip` + `mask` | Required when `routed: true` |
| `ip` format | Must be valid IPv4 address |
| `mask` format | Must be valid IPv4 address |

## Pipeline Position

```text
load_inventory.py loads YAML
        ↓
core/validator.py validates ALL devices + interfaces
        ↓
PASS → continue to SSH connection
FAIL → log all errors + abort before touching any device
```

## Example — Validation Passed

```bash
2026-05-26 18:34:39 | INFO  | [EXEC-...] | Validating inventory schema...
2026-05-26 18:34:39 | INFO  | [EXEC-...] | Inventory validation passed — 1 device(s), 3 interface(s)
```

## Example — Validation Failed

```bash
2026-05-26 18:35:54 | INFO  | [EXEC-...] | Validating inventory schema...
2026-05-26 18:35:54 | ERROR | [EXEC-...] | Inventory validation failed:
2026-05-26 18:35:54 | ERROR | [EXEC-...] |   interfaces[0]: ip is required when routed is True
2026-05-26 18:35:54 | ERROR | [EXEC-...] | Aborting — fix inventory before retrying
```

No connection was made. No device was touched.

## Key Engineering Principle Applied

> Never connect to a device with unvalidated data.
> Validate at the boundary — before the network, not during.

---

# PHASE 13 — Multi-Device Orchestration

## Objective

Scale the framework from single-device to multi-device execution
with both sequential and parallel processing modes.

## Features Implemented

- `scripts/core/orchestrator.py` — new module
- `process_device()` — full pipeline for a single device, thread-safe
- `run_parallel()` — `ThreadPoolExecutor` concurrent execution
- `--parallel` CLI flag added to `main.py`
- `label` field in `devices.yml` — device identity for filenames and logs
- Non-Netmiko fields stripped before SSH connection (`label`, etc.)
- Per-device log files scoped correctly in parallel mode using thread lock
- Separate output files per device (backups, configs, reports, logs)

## Usage

```bash
# Sequential — one device at a time
python scripts/main.py

# Parallel — all devices simultaneously
python scripts/main.py --parallel

# Either mode with dry-run
python scripts/main.py --dry-run
python scripts/main.py --parallel --dry-run
```

## devices.yml with Labels

```yaml
devices:
  - host: devnetsandboxiosxec9k.cisco.com
    device_type: cisco_xe
    label: device-1

  - host: devnetsandboxiosxec9k.cisco.com
    device_type: cisco_xe
    label: device-2
```

Labels ensure separate output files even when two entries share the same host.

## Output Files Per Device

```text
backups/
├── backup_device-1_20260531_163434.txt
└── backup_device-2_20260531_163434.txt

configs/generated/
├── config_device-1_20260531_163434.txt
└── config_device-2_20260531_163434.txt

reports/html/
├── report_device-1_20260531_163434.html
└── report_device-2_20260531_163434.html

logs/
├── netdevops.log
├── device-1.log
└── device-2.log
```

## Key Learning — Non-Netmiko Fields

When `ConnectHandler(**device)` is called, ALL dictionary keys are passed
to Netmiko. Any custom field like `label` causes an immediate failure:

```
BaseConnection.__init__() got an unexpected keyword argument 'label'
```

Fix in `core/connection.py`:

```python
netmiko_params = {
    k: v for k, v in device.items()
    if k not in ("label",)
}
conn = ConnectHandler(**netmiko_params)
```

## Parallel Execution Proven

Both threads launched simultaneously — confirmed by identical timestamps:

```bash
16:35:43 | Connecting to devnetsandboxiosxec9k.cisco.com...  ← thread 1
16:35:43 | Connecting to devnetsandboxiosxec9k.cisco.com...  ← thread 2
16:35:45 | [device-2] [OK] GigabitEthernet1/0/2 → COMPLIANT
16:35:45 | [device-1] [OK] GigabitEthernet1/0/2 → COMPLIANT
16:35:46 | [device-1] Processing complete ✔
16:35:46 | [device-2] Processing complete ✔
```

## Sequential Live Run — Idempotency in Multi-Device Context

The sequential live run demonstrated an important real-world behavior:

```bash
# device-1 processed first
[device-1] [DRIFT] GigabitEthernet1/0/2 → DRIFT
[device-1] Remediation successful — GigabitEthernet1/0/2

# device-2 processed second — config already fixed by device-1
[device-2] [OK] GigabitEthernet1/0/2 → COMPLIANT
[device-2] All interfaces COMPLIANT — no remediation needed
```

Device-1 remediated the interfaces. By the time Device-2 connected,
the device was already compliant. This is exactly how idempotent
multi-device automation behaves in production.

---

# PHASE 14 — RESTCONF Integration

## Objective

Add a second, API-native compliance validation layer alongside
the existing Netmiko SSH layer. RESTCONF retrieves structured
JSON directly from the device API — no text parsing required.

## Features Implemented

- `scripts/core/restconf.py` — new module
- `get_restconf_interfaces()` — HTTPS GET to IETF interfaces endpoint
- `parse_restconf_interfaces()` — converts JSON response to flat dict
- `restconf_compliance_check()` — field-by-field comparison against desired state
- Integrated into `orchestrator.py` after remediation
- RESTCONF results included in JSON and HTML reports
- `restconf_port: 443` field added to `devices.yml`
- SSL verification disabled for DevNet sandbox self-signed certs

## RESTCONF vs Netmiko Comparison

| | Netmiko (Layer 1) | RESTCONF (Layer 2) |
|---|---|---|
| Transport | SSH | HTTPS |
| Data format | CLI text | Structured JSON |
| Parsing | Line-by-line extraction | Direct field access |
| Purpose | Compliance + Remediation | API-native verification |
| Speed | Slower | Faster |

## Pipeline Position

```text
Netmiko SSH compliance check  ← Layer 1
        ↓
Remediation (if DRIFT)
        ↓
RESTCONF compliance check     ← Layer 2 (NEW)
        ↓
JSON + HTML reports (both layers)
```

## RESTCONF Endpoint

```
GET https://{host}:443/restconf/data/ietf-interfaces:interfaces
Headers: Accept: application/yang-data+json
Auth: HTTP Basic (same credentials from .env)
```

## Dual-Layer Validation Proven

### Dry-Run — RESTCONF detects existing drift

```bash
[device-1] RESTCONF GET successful
[device-1] RESTCONF [GigabitEthernet1/0/2] DRIFT — description: expected 'YAML LAB1' got 'PC2_Engineering'
[device-1] RESTCONF [GigabitEthernet1/0/2] DRIFT — ip: expected '10.10.10.1' got 'None'
[device-1] RESTCONF [GigabitEthernet1/0/4] DRIFT — enabled: expected 'True' got 'False'
```

### Live — RESTCONF confirms remediation worked

```bash
[device-1] Remediation successful — GigabitEthernet1/0/2
[device-1] Remediation successful — GigabitEthernet1/0/3
[device-1] Remediation successful — GigabitEthernet1/0/4
[device-1] RESTCONF GET successful
[device-1] RESTCONF [GigabitEthernet1/0/2] → COMPLIANT
[device-1] RESTCONF [GigabitEthernet1/0/3] → COMPLIANT
[device-1] RESTCONF [GigabitEthernet1/0/4] → COMPLIANT
```

📄 [View RESTCONF Drift Dashboard — device-1](../images/screenshoots/RESTCONF_DRIFT_DASHBOARD_device1.png)

📄 [View RESTCONF Compliant Dashboard — device-2](../images/screenshoots/RESTCONF_COMPLIANT_DASHBOARD_device2.png)

## HTML Report Enhancement

Each interface card in the HTML dashboard now shows:

```
[COMPLIANT] GigabitEthernet1/0/2
Expected (desired state): ...
Actual (on device): ...
RESTCONF Validation: COMPLIANT  ← new
```

## Key Engineering Principle Applied

> One validation layer catches what you know to check.
> Two validation layers catch what you didn't think to check.
> RESTCONF confirms via the device API what Netmiko confirmed via CLI.

---

# PHASE 15 — Flask Compliance Dashboard

## Objective

Build a web-based UI that reads existing JSON reports and presents
compliance status, RESTCONF results, and execution history in a browser.
No database required — the `reports/json/` files are the data source.

## Features Implemented

- `dashboard/app.py` — Flask application
- `dashboard/templates/base.html` — shared layout with sticky navbar
- `dashboard/templates/index.html` — overview page with summary cards, device status, execution history, and run controls
- `dashboard/templates/report.html` — detailed report view per run
- `dashboard/templates/logs.html` — live log viewer with color-coded lines
- `dashboard/static/style.css` — dark terminal-inspired theme

## Dashboard Structure

```
dashboard/
├── app.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── report.html
│   └── logs.html
└── static/
    └── style.css
```

## Pages and Routes

| Route | Page | What it shows |
|---|---|---|
| `/` | Overview | Summary cards, latest device status, execution history |
| `/report/<filename>` | Report Detail | Full compliance + RESTCONF results per interface |
| `/logs` | Execution Logs | Last 50 lines of `logs/netdevops.log` with color coding |
| `POST /run` | — | Triggers `main.py` from browser, returns stdout as JSON |
| `/api/logs` | — | Log lines as JSON for live refresh |
| `/api/summary` | — | Compliance summary as JSON |

## How to Run

```bash
# From project root
python dashboard/app.py

# Open browser at:
http://127.0.0.1:5000
```

## Design

- Dark terminal theme (`#0d1117` background — GitHub dark)
- Green (`#3fb950`) for COMPLIANT, Red (`#f85149`) for DRIFT
- Monospace font for all device and config data
- Responsive grid layout
- Modal popup for run output
- Sticky navbar with Overview and Logs links

## Dashboard Screenshots

### Overview Page

📄 [View Dashboard Overview — Run 1](../images/screenshoots/FLASK_DASHBOARD_OVERVIEW.png)

📄 [View Dashboard Overview — Run 2](../images/screenshoots/FLASK_DASHBOARD_OVERVIEW_2.png)

📄 [View Dashboard Overview — Run 3](../images/screenshoots/FLASK_DASHBOARD_OVERVIEW_3.png)

### Report Detail Page

📄 [View Report Detail — Run 1](../images/screenshoots/FLASK_DASHBOARD_REPORT_DETAIL.png)

📄 [View Report Detail — Run 2](../images/screenshoots/FLASK_DASHBOARD_REPORT_DETAIL_2.png)

📄 [View Execution History — Run 3](../images/screenshoots/FLASK_DASHBOARD_REPORT_DETAIL_3.png)

### Logs Page

📄 [View Logs Page — Run 1](../images/screenshoots/FLASK_DASHBOARD_LOGS.png)

📄 [View Logs Page — Run 2](../images/screenshoots/FLASK_DASHBOARD_LOGS_2.png)

## Key Engineering Principle Applied

> Compliance data is only useful if it's visible.
> The dashboard turns JSON reports into actionable insights
> without requiring any new data infrastructure.

---

# PHASE 16 — Connection Hardening

## Objective

Improve SSH connection reliability on DevNet sandbox devices
that exhibit non-standard behavior including slow initialization,
non-standard prompts, and user EXEC mode landing.

## Features Implemented

- `global_delay_factor = 4` — increased from 2 for slower sandbox response
- `fast_cli = False` — disables fast mode for better prompt detection
- `conn_timeout = 15` — extended connection timeout
- `session_timeout = 60` — extended session timeout
- Non-Netmiko fields stripped before `ConnectHandler`:
  `label`, `restconf_port` excluded from SSH params

## Key Learning — Shared Sandbox Behavior

DevNet Always-On sandboxes are shared resources with known issues:

- Other users can reset device config at any time
- SSH port may be open but AAA service not yet initialized
- Credentials are dynamic and unique per reservation
- Device may land at user EXEC (`R1>`) instead of privileged (`R1#`)
- Sandbox infrastructure can experience authentication failures
  affecting all users simultaneously (confirmed in DevNet community)

## Key Learning — Non-Netmiko Fields Must Be Stripped

Any custom field added to `devices.yml` must be excluded
before passing to `ConnectHandler`:

```python
netmiko_params = {
    k: v for k, v in device.items()
    if k not in ("label", "restconf_port")
}
```

Failing to strip custom fields causes immediate connection failure:
```
BaseConnection.__init__() got an unexpected keyword argument 'label'
```

## Sandbox Troubleshooting Checklist

When sandbox authentication fails:

1. Verify TCP port 22 is open: `socket.create_connection(host, 22)`
2. Verify credentials load correctly from `.env`
3. Test manual SSH before running framework
4. Check if sandbox session has expired (3-day limit)
5. Launch a new reservation and wait 5-10 minutes
6. Check DevNet community for known infrastructure issues
7. Try with `look_for_keys=False` and `allow_agent=False`

---

# 📊 Current Capabilities

## Successfully Implemented

- Multi-interface automation
- YAML inventory loading
- YAML schema validation (Pydantic — pre-connection)
- Jinja2 templating
- Drift detection (Netmiko CLI)
- Compliance validation (dual-layer: Netmiko + RESTCONF)
- Automated remediation (full config push)
- RESTCONF API integration (`core/restconf.py`)
- Structured logging (rotating, console + file)
- Execution IDs (per-run traceability)
- Per-device log files
- Rendered config archival (`configs/generated/`)
- Dry-run mode (`--dry-run` flag)
- Modular `core/` architecture (`main.py` + 9 focused modules)
- Sequential multi-device orchestration
- Parallel multi-device orchestration (`--parallel` flag)
- Device labeling for output file separation
- Flask compliance dashboard (`dashboard/`)
- HTML dashboard generation (with RESTCONF validation section)
- JSON structured reporting (includes RESTCONF results)
- Local backup generation
- Idempotent re-runs (proven in single and multi-device)
- GitHub Actions CI/CD pipeline

---

# 📁 Current Project Structure

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
│       ├── FULL_CONSOLIDATED_NETDEVOPS_SCRIPT_V3.py
│       ├── FULL_CONSOLIDATED_NETDEVOPS_SCRIPT_V4.py
│       ├── FULL_CONSOLIDATED_NETDEVOPS_SCRIPT_V5.py
│       ├── FULL_CONSOLIDATED_NETDEVOPS_SCRIPT_V6.py
│       └── NETDEVOPS_DOCUMENTATION_V1.md
├── dashboard/
│   ├── app.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── report.html
│   │   └── logs.html
│   └── static/
│       └── style.css
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
│   ├── netdevops.log
│   ├── device-1.log
│   └── device-2.log
├── reports/
│   ├── html/
│   └── json/
├── scripts/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── backup.py
│   │   ├── rendering.py
│   │   ├── compliance.py
│   │   ├── remediation.py
│   │   ├── reporting.py
│   │   ├── validator.py
│   │   ├── orchestrator.py
│   │   └── restconf.py
│   ├── load_inventory.py
│   ├── logger.py
│   └── main.py
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
- validate at the boundary (schema check before connecting)
- scale horizontally (parallel execution over sequential waiting)
- make it visible (compliance data belongs in a dashboard)

---

# 🚧 Current Limitations

- Single vendor focus (Cisco IOS-XE)
- No database-backed inventory yet
- No scheduled compliance jobs yet
- `tests/` directory empty — no automated test coverage yet
- Flask dashboard runs in development mode only
- DevNet Always-On sandbox is a shared resource — other users
  can reset device config at any time causing unexpected DRIFT

---

# 🚀 Planned Roadmap

## Short-Term

- PyATS/Genie validation
- Scheduled compliance jobs

## Mid-Term

- CSV/Excel inventory support
- Configuration archival
- Flask dashboard production deployment (gunicorn/nginx)

## Long-Term

- Intent-based networking
- Real-time compliance engine
- Multi-vendor support

---

# ✍️ Maintainer

Cyprien Carlos Temateu

NetDevOps / Network Automation Practice Lab