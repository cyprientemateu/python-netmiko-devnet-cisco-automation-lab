from netmiko import ConnectHandler
from datetime import datetime
import json
import difflib
import os
import yaml
from dotenv import load_dotenv

# =========================
# LOAD ENVIRONMENT VARIABLES
# =========================
load_dotenv()

# =========================
# CREATE PROJECT FOLDERS
# =========================
os.makedirs("scripts", exist_ok=True)
os.makedirs("backups", exist_ok=True)
os.makedirs("reports/json", exist_ok=True)
os.makedirs("reports/html", exist_ok=True)

# =========================
# 1. LOAD INVENTORY FROM YAML
# =========================
with open("inventory/devices.yml") as f:
    inventory = yaml.safe_load(f)

devices = inventory["devices"]

# Inject credentials from .env
for device in devices:
    device["username"] = os.getenv("NET_USERNAME")
    device["password"] = os.getenv("NET_PASSWORD")

# =========================
# 2. DESIRED STATE (SOURCE OF TRUTH)
# =========================
desired_config = {
    "GigabitEthernet1/0/2": {
        "description": "LAB1",
        "ip": "10.20.30.1",
        "mask": "255.255.255.0"
    },
    "GigabitEthernet1/0/3": {
        "description": "LAB2"
    },
    "GigabitEthernet1/0/4": {
        "description": "LAB3",
        "ip": "10.20.40.1",
        "mask": "255.255.255.0"
    }
}

# =========================
# 3. CONNECT FUNCTION
# =========================
def connect(device):
    print(f"\nConnecting to {device['host']}...")
    return ConnectHandler(**device)

# =========================
# 4. GET RUNNING CONFIG
# =========================
def get_running_config(conn):
    return conn.send_command("show running-config")

# =========================
# 5. DIFF ENGINE
# =========================
def diff_configs(desired, actual):

    diff_report = {}
    actual_lines = actual.splitlines()

    for intf, config in desired.items():

        expected_lines = [f"interface {intf}"]

        if "description" in config:
            expected_lines.append(
                f" description {config['description']}"
            )

        if "ip" in config:
            expected_lines.append(" no switchport")
            expected_lines.append(
                f" ip address {config['ip']} {config['mask']}"
            )

        diff = list(
            difflib.unified_diff(
                expected_lines,
                actual_lines,
                lineterm=""
            )
        )

        diff_report[intf] = diff

    return diff_report

# =========================
# 6. COMPLIANCE ENGINE
# =========================
def compliance_check(diff_report):

    results = {}

    for intf, diff in diff_report.items():

        if len(diff) == 0:
            results[intf] = "COMPLIANT"
        else:
            results[intf] = "DRIFT"

    return results

# =========================
# 7. REMEDIATION ENGINE
# =========================
def remediate(conn, compliance):

    for intf, status in compliance.items():

        if status == "DRIFT":

            print(f"\nRemediating {intf}...")

            cfg = [
                f"interface {intf}",
                "no shutdown"
            ]

            conn.send_config_set(cfg)

# =========================
# 8. HTML REPORT GENERATOR
# =========================
def generate_html_report(compliance, diff_report, filename):

    html = """
    <html>
    <head>
        <title>Network Compliance Report</title>

        <style>
            body {
                font-family: Arial;
                margin: 40px;
            }

            .ok {
                color: green;
            }

            .fail {
                color: red;
            }

            pre {
                background-color: #f4f4f4;
                padding: 10px;
                border-radius: 5px;
            }
        </style>

    </head>

    <body>

    <h1>Network Compliance Report</h1>
    """

    for intf, status in compliance.items():

        color = "ok" if status == "COMPLIANT" else "fail"

        html += f"<h3 class='{color}'>{intf} - {status}</h3>"

        html += "<pre>"

        for line in diff_report[intf]:
            html += line + "\n"

        html += "</pre>"

    html += "</body></html>"

    with open(filename, "w") as f:
        f.write(html)

# =========================
# 9. MAIN EXECUTION ENGINE
# =========================
def main():

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for device in devices:

        # -------------------------
        # CONNECT
        # -------------------------
        conn = connect(device)

        # -------------------------
        # GET RUNNING CONFIG
        # -------------------------
        print("\nCollecting running config...")

        actual = get_running_config(conn)

        # -------------------------
        # BACKUP
        # -------------------------
        backup_file = (
            f"backups/backup_"
            f"{device['host']}_{timestamp}.txt"
        )

        with open(backup_file, "w") as f:
            f.write(actual)

        print(f"\nBackup saved: {backup_file}")

        # -------------------------
        # DIFF ENGINE
        # -------------------------
        print("\nRunning diff engine...")

        diff_report = diff_configs(
            desired_config,
            actual
        )

        # -------------------------
        # COMPLIANCE CHECK
        # -------------------------
        print("\nRunning compliance check...")

        compliance = compliance_check(diff_report)

        for interface, result in compliance.items():
            print(f"{interface} → {result}")

        # -------------------------
        # REMEDIATION
        # -------------------------
        print("\nRunning remediation...")

        remediate(conn, compliance)

        # -------------------------
        # REPORT FILES
        # -------------------------
        json_file = (
            f"reports/json/"
            f"report_{timestamp}.json"
        )

        html_file = (
            f"reports/html/"
            f"report_{timestamp}.html"
        )

        with open(json_file, "w") as f:

            json.dump(
                {
                    "device": device["host"],
                    "compliance": compliance,
                    "diff": {
                        k: str(v)
                        for k, v in diff_report.items()
                    }
                },
                f,
                indent=4
            )

        generate_html_report(
            compliance,
            diff_report,
            html_file
        )

        # -------------------------
        # DISCONNECT
        # -------------------------
        conn.disconnect()

        print("\nDONE ✔")
        print(f"JSON Report: {json_file}")
        print(f"HTML Report: {html_file}")

# =========================
# RUN SCRIPT
# =========================
if __name__ == "__main__":
    main()