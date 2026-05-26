from netmiko import ConnectHandler
from datetime import datetime
import json
import difflib
import os
from load_inventory import load_devices, load_interfaces
from logger import get_logger

# =========================
# LOGGER
# =========================
log = get_logger()

# =========================
# CREATE PROJECT FOLDERS
# =========================
os.makedirs("backups", exist_ok=True)
os.makedirs("reports/json", exist_ok=True)
os.makedirs("reports/html", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# =========================
# 1. LOAD INVENTORY
# =========================
devices    = load_devices()
interfaces = load_interfaces()

# =========================
# 2. BUILD EXPECTED CONFIG LINES
# =========================
def build_expected_lines(intf):
    """
    Builds the list of sub-commands we expect to find
    inside the interface block on the device.

    Rules:
    - No leading spaces: we normalize both sides before comparing.
    - No interface header line: extract_interface_block strips it.
    - No 'no shutdown': Cisco IOS omits this from running-config
      when an interface is up — it is the default and invisible.
      We only check for 'shutdown' when the interface should be down.
    """
    lines = []
    lines.append(f"description {intf['description']}")

    if intf.get("routed"):
        lines.append("no switchport")
        lines.append(f"ip address {intf['ip']} {intf['mask']}")

    if not intf.get("enabled"):
        lines.append("shutdown")

    return lines

# =========================
# 3. CONNECT FUNCTION
# =========================
def connect(device):
    log.info(f"Connecting to {device['host']}...")
    try:
        conn = ConnectHandler(**device)
        log.info(f"Connection established — {device['host']}")
        return conn
    except Exception as e:
        log.error(f"Connection failed — {device['host']} — {e}")
        raise

# =========================
# 4. GET RUNNING CONFIG
# =========================
def get_running_config(conn):
    log.info("Collecting running config...")
    return conn.send_command("show running-config")

# =========================
# 5. EXTRACT INTERFACE BLOCK
# =========================
def extract_interface_block(running_config, interface_name):
    """
    Extracts sub-command lines for a specific interface
    from the full running config.

    - Skips the interface header line itself.
    - Strips leading/trailing whitespace from each line
      so comparison with expected lines is normalized.
    - Stops at the next interface block or '!' marker.
    """
    lines    = running_config.splitlines()
    block    = []
    in_block = False

    for line in lines:

        if line.strip().lower() == f"interface {interface_name.lower()}":
            in_block = True
            continue

        if in_block:
            if line.startswith("interface ") or line.strip() == "!":
                break
            if line.strip():
                block.append(line.strip())

    return block

# =========================
# 6. DIFF ENGINE
# =========================
def diff_configs(interfaces, running_config):
    """
    For each interface, checks whether all expected lines
    are present in the actual device block.

    Uses subset logic — not exact match — because:
    - Cisco adds lines we don't control (negotiation auto,
      spanning-tree, etc.)
    - An exact diff would always show DRIFT due to those extras.
    - We only care that OUR desired lines are present.
    """
    diff_report = {}

    for intf in interfaces:

        name     = intf["interface"]
        expected = build_expected_lines(intf)
        actual   = extract_interface_block(running_config, name)

        missing = [
            line for line in expected
            if line not in actual
        ]

        diff = list(
            difflib.unified_diff(
                expected,
                actual,
                fromfile="desired",
                tofile="actual",
                lineterm=""
            )
        )

        diff_report[name] = {
            "expected": expected,
            "actual":   actual,
            "missing":  missing,
            "diff":     diff
        }

    return diff_report

# =========================
# 7. COMPLIANCE ENGINE
# =========================
def compliance_check(diff_report):

    results = {}

    for intf, data in diff_report.items():

        if not data["missing"]:
            results[intf] = "COMPLIANT"
        else:
            results[intf] = "DRIFT"

    return results

# =========================
# 8. REMEDIATION ENGINE
# =========================
def remediate(conn, compliance, interfaces):

    any_drift = any(
        status == "DRIFT"
        for status in compliance.values()
    )

    if not any_drift:
        log.info("All interfaces COMPLIANT — no remediation needed")
        return

    for intf in interfaces:

        name   = intf["interface"]
        status = compliance.get(name)

        if status == "DRIFT":

            log.warning(f"Remediating {name}...")

            try:
                cfg = [f"interface {name}"]
                cfg.append(f"description {intf['description']}")

                if intf.get("routed"):
                    cfg.append("no switchport")
                    cfg.append(
                        f"ip address {intf['ip']} {intf['mask']}"
                    )
                else:
                    cfg.append("switchport")

                if intf.get("enabled"):
                    cfg.append("no shutdown")
                else:
                    cfg.append("shutdown")

                conn.send_config_set(cfg)
                log.info(f"Remediation successful — {name}")

            except Exception as e:
                log.error(f"Remediation failed — {name} — {e}")

# =========================
# 9. HTML REPORT GENERATOR
# =========================
def generate_html_report(compliance, diff_report, device_host, filename):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <html>
    <head>
        <title>NetDevOps Compliance Report</title>
        <style>
            body      {{ font-family: Arial; margin: 40px;
                         background: #f9f9f9; }}
            h1        {{ color: #333; }}
            h2        {{ color: #555; font-size: 14px; }}
            h3        {{ margin-bottom: 4px; }}
            .compliant {{ color: green; }}
            .drift     {{ color: red; }}
            .section  {{ background: white; border: 1px solid #ddd;
                         border-radius: 6px; padding: 16px;
                         margin-bottom: 20px; }}
            pre       {{ background: #f4f4f4; padding: 10px;
                         border-radius: 4px; font-size: 13px; }}
            .add      {{ color: green; }}
            .rem      {{ color: red; }}
        </style>
    </head>
    <body>
    <h1>NetDevOps Compliance Report</h1>
    <h2>Device: {device_host} &nbsp;|&nbsp; Generated: {timestamp}</h2>
    <hr>
    """

    for intf, status in compliance.items():

        css  = "compliant" if status == "COMPLIANT" else "drift"
        data = diff_report[intf]

        html += f"<div class='section'>"
        html += f"<h3 class='{css}'>[{status}] {intf}</h3>"

        html += "<b>Expected (desired state):</b><pre>"
        for line in data["expected"]:
            html += line + "\n"
        html += "</pre>"

        html += "<b>Actual (on device):</b><pre>"
        for line in data["actual"]:
            html += line + "\n"
        html += "</pre>"

        if data["missing"]:
            html += "<b>Missing lines (causing DRIFT):</b><pre>"
            for line in data["missing"]:
                html += f"<span class='rem'>- {line}</span>\n"
            html += "</pre>"

        html += "</div>"

    html += "</body></html>"

    with open(filename, "w") as f:
        f.write(html)

# =========================
# 10. MAIN EXECUTION ENGINE
# =========================
def main():

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    log.info("=" * 50)
    log.info("NetDevOps Framework V4 — Execution Started")
    log.info("=" * 50)

    for device in devices:

        log.info(f"Processing device: {device['host']}")

        # -------------------------
        # CONNECT
        # -------------------------
        try:
            conn = connect(device)
        except Exception:
            log.error(f"Skipping {device['host']} — could not connect")
            continue

        # -------------------------
        # BACKUP
        # -------------------------
        try:
            actual      = get_running_config(conn)
            backup_file = (
                f"backups/backup_{device['host']}_{timestamp}.txt"
            )
            with open(backup_file, "w") as f:
                f.write(actual)
            log.info(f"Backup saved — {backup_file}")

        except Exception as e:
            log.error(f"Backup failed — {device['host']} — {e}")
            conn.disconnect()
            continue

        # -------------------------
        # DIFF ENGINE
        # -------------------------
        log.info("Running diff engine...")
        diff_report = diff_configs(interfaces, actual)

        # -------------------------
        # COMPLIANCE CHECK
        # -------------------------
        log.info("Running compliance check...")
        compliance = compliance_check(diff_report)

        for intf, result in compliance.items():
            if result == "COMPLIANT":
                log.info(f"[OK]    {intf} → {result}")
            else:
                log.warning(f"[DRIFT] {intf} → {result}")

        # -------------------------
        # REMEDIATION
        # -------------------------
        log.info("Running remediation engine...")
        remediate(conn, compliance, interfaces)

        # -------------------------
        # REPORTS
        # -------------------------
        json_file = f"reports/json/report_{timestamp}.json"
        html_file = f"reports/html/report_{timestamp}.html"

        try:
            with open(json_file, "w") as f:
                json.dump(
                    {
                        "device":     device["host"],
                        "timestamp":  timestamp,
                        "compliance": compliance,
                        "diff": {
                            k: {
                                "expected": v["expected"],
                                "actual":   v["actual"],
                                "missing":  v["missing"],
                                "diff":     v["diff"]
                            }
                            for k, v in diff_report.items()
                        }
                    },
                    f,
                    indent=4
                )

            generate_html_report(
                compliance,
                diff_report,
                device["host"],
                html_file
            )

            log.info(f"JSON report saved — {json_file}")
            log.info(f"HTML report saved — {html_file}")

        except Exception as e:
            log.error(f"Report generation failed — {e}")

        # -------------------------
        # DISCONNECT
        # -------------------------
        conn.disconnect()
        log.info(f"Disconnected from {device['host']}")

    log.info("=" * 50)
    log.info("NetDevOps Framework V4 — Execution Complete")
    log.info("=" * 50)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()