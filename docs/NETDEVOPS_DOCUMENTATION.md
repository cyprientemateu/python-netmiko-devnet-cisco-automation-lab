# 📘 NetDevOps Practice Documentation (Engineering Journal)

## 🧭 Purpose
This document is the engineering journal for the NetDevOps automation project. It tracks:

- architecture evolution
- technical decisions
- lessons learned
- debugging insights
- automation maturity improvements

It is updated only when meaningful changes occur.

---

## 📌 Project Summary

This project focuses on building a NetDevOps automation framework using:

- Python
- Netmiko
- Cisco IOS-XE (DevNet Sandbox)

It has evolved from basic SSH automation into a structured automation system including:

- interface provisioning
- compliance validation
- drift detection
- remediation workflows
- reporting (JSON + HTML)
- backup strategy

---

## 🏗 Architecture Evolution

### Core Pipeline

Connect → Collect → Compare → Validate → Remediate → Report

### Modules Implemented
1. Device Connection Layer
- Netmiko SSH session management

2. Data Collection Layer
- **show running-config**
- **show ip interface brief**

3. State Engine
- Desired state defined in Python dictionary
- Acts as source of truth

4. Diff Engine
- Uses **difflib**
- Detects configuration drift

5. Compliance Engine
- Classifies interfaces as:
    - COMPLIANT
    - DRIFT

6. Remediation Engine
- Applies corrective configuration automatically

7. Reporting Engine
- JSON machine-readable report
- HTML visual dashboard

8. Backup System
- Timestamped backups stored locally
- Another backup stored on the device
- Organized into **/backups**

---

## 🧠 Key Learnings

### 1. Layer-2 vs Layer-3 Interfaces

Issue

IP assignment failed initially:
```bash
% Invalid input detected
```
Root Cause

Interface was in Layer-2 mode (switchport enabled)

Fix
```bash
no switchport
```

**NOTES**
Must use:
no switchport
before assigning IPs.

---

### 2. Automation Safety Model
Correct automation order:
```
Backup → Diff → Validate → Remediate
```

---

### 3. Netmiko Behavior Insights
- **send_config_set()** handles configuration mode automatically
- Some IOS commands require timing awareness
- Validation requires structured parsing (TextFSM optional)

---

### 4. Drift Detection
Early implementation used raw diff comparison.

Improvement direction:
- Moving from text diff → intent-based validation.
- avoid false drift detection due to formatting differences

---

## 📊 Current Capabilities

- Successful execution outputs:
```bash
COMPLIANT → interfaces aligned with desired state
DRIFT → mismatch detected and remediated
```
- Multi-interface automation
- Compliance engine
- JSON + HTML reporting
- Backup system
- Remediation engine

---

📁 Project Structure

D:.
├───backups
├───reports
│   ├───html
│   └───json
├───scripts
└───docs       

---

## 🚧 Known Limitations

- Simple diff engine still in use
- No centralized inventory system yet
- No CI/CD pipeline integration yet
- No logging framework (loguru / logging module not implemented)

---

## 🚀 Roadmap

- Intent-based compliance engine
- YAML/CSV inventory integration
- GitHub Actions CI/CD pipeline
- Logging system
- API dashboard
- Configuration templating (Jinja2)

---

🧪 Operational Principles

This project follows:

- Backup before change
- Validate after change
- Automate remediation safely
- Maintain idempotency
- Prefer declarative configuration models

---

## ✍️ Maintainer
Cyprien Carlos Temateu
NetDevOps / Network Automation Practice Lab
