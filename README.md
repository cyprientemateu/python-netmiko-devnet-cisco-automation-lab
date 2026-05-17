# 📘 NetDevOps Automation Project (Netmiko + Cisco IOS-XE)

## 🧭 Project Overview

This project demonstrates real-world NetDevOps automation practices using Python and Netmiko against Cisco IOS-XE devices (DevNet Sandbox).

It has evolved from simple SSH command execution into a full automation framework including:

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

### ✅ Safety & Reliability
- Pre-change configuration backup
- Post-change validation
- Automatic rollback support
- Idempotent execution (safe re-runs)

### ✅ Compliance Engine
- Desired state vs actual state comparison
- Drift detection
- Compliance classification

### ️✅ Reporting System
- JSON structured reports
- HTML dashboard reports
- Timestamped outputs

---

## 🏗 Architecture

Connect → Collect State → Compare → Validate → Remediate → Report

---

## 🧰 Technologies Used

- Python 3.11
- Netmiko
- Cisco IOS-XE (DevNet Sandbox)
- TextFSM
- HTML + JSON reporting
- PowerShell

---

## 📁 Project Structure

python-netmiko-devnet-cisco/
│
├── backups/
│
├── configs/
│
├── docs/
│   ├── NETDEVOPS_DOCUMENTATION.md
│
├── inventory/
│
├── reports/
│   ├── html/
│   └── json/
│
├── scripts/
│
├── templates/
│
├── tests/
│
├── .gitignore
├── requirements.txt
├── README.md
└── LICENSE

---

## ⚙️ How It Works

### 1️⃣ Backup Phase
- Captures running configuration
- Stores timestamped backup in /backups

### 2️⃣ Diff Engine
- Compares desired state vs actual device state

### 3️⃣ Compliance Engine
- Classifies:
    - COMPLIANT
    - DRIFT

### 4️⃣ Remediation
- Fixes drift automatically when detected

### 5️⃣ Reporting
- Generates:
    - JSON report (machine-readable)
    - HTML dashboard (visual report)

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
```
Then apply:
```bash
ip address X.X.X.X X.X.X.X
```

---

## 📊 Example Output

```bash
[OK] GigabitEthernet1/0/2 → COMPLIANT
[DRIFT] GigabitEthernet1/0/3 → REMEDIATED

JSON Report: reports/json/report_xxx.json
HTML Report: reports/html/report_xxx.html
```

---

## 🔐 Best Practices Used

- Always backup before changes
- Validate after configuration
- Avoid manual verification
- Ensure idempotent automation
- Use structured reporting

---

## 🚀 Future Improvements

- YAML/CSV inventory
- Multi-device orchestration
- CI/CD pipeline
- API dashboard
- Jinja2 templating

---

## 🧪 Learning Outcome

This project demonstrates:

- Real-world network automation design
- Infrastructure as Code thinking
- Validation-first engineering approach
- Scalable automation architecture

---

## ✍️ Maintainer
Cyprien Carlos Temateu
NetDevOps Practice Lab
