import argparse
import os
from datetime import datetime

from load_inventory import load_devices, load_interfaces
from logger         import get_logger, add_device_handler, remove_device_handler

from core.connection  import connect, get_running_config
from core.backup      import save_backup
from core.rendering   import render_and_save_configs
from core.compliance  import diff_configs, compliance_check
from core.remediation import remediate
from core.reporting   import save_json_report, generate_html_report
from core.validator   import validate_inventory

# =========================
# CREATE PROJECT FOLDERS
# =========================
os.makedirs("backups", exist_ok=True)
os.makedirs("configs/generated", exist_ok=True)
os.makedirs("reports/json", exist_ok=True)
os.makedirs("reports/html", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# =========================
# ARGUMENT PARSER
# =========================
parser = argparse.ArgumentParser(
    description="NetDevOps Automation Framework"
)
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Run validation only — no changes pushed to device"
)
args = parser.parse_args()

EXECUTION_MODE = "DRY-RUN" if args.dry_run else "LIVE"

# =========================
# LOAD INVENTORY
# =========================
devices    = load_devices()
interfaces = load_interfaces()

# =========================
# MAIN PIPELINE
# =========================
def main():

    # -------------------------
    # EXECUTION ID
    # Unique identifier for this run.
    # Stamped on every log line for full traceability.
    # Format: EXEC-YYYYMMDD-HHMMSS
    # -------------------------
    timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    execution_id = f"EXEC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    log = get_logger(execution_id=execution_id)

    log.info("=" * 60)
    log.info(f"NetDevOps Framework — {EXECUTION_MODE} MODE")
    log.info(f"Execution ID: {execution_id}")
    log.info("=" * 60)

    # -------------------------
    # SCHEMA VALIDATION
    # Validates all devices and interfaces against
    # Pydantic models before any connection is made.
    # Aborts immediately if any errors are found.
    # -------------------------
    log.info("Validating inventory schema...")
    errors = validate_inventory(devices, interfaces)

    if errors:
        log.error("Inventory validation failed:")
        for error in errors:
            log.error(f"  {error}")
        log.error("Aborting — fix inventory before retrying")
        return

    log.info(
        f"Inventory validation passed — "
        f"{len(devices)} device(s), {len(interfaces)} interface(s)"
    )

    for device in devices:

        log.info(f"Processing device: {device['host']}")

        # -------------------------
        # PER-DEVICE LOG
        # Adds logs/{device_host}.log for this device's run
        # -------------------------
        add_device_handler(device["host"])

        # -------------------------
        # CONNECT
        # -------------------------
        try:
            conn = connect(device)
        except Exception:
            log.error(f"Skipping {device['host']} — could not connect")
            remove_device_handler(device["host"])
            continue

        # -------------------------
        # BACKUP
        # -------------------------
        try:
            actual = get_running_config(conn)
            save_backup(actual, device["host"], timestamp)
        except Exception as e:
            log.error(f"Backup failed — {device['host']} — {e}")
            conn.disconnect()
            remove_device_handler(device["host"])
            continue

        # -------------------------
        # RENDER + SAVE CONFIGS
        # -------------------------
        config_file = render_and_save_configs(
            interfaces,
            device["host"],
            timestamp,
            EXECUTION_MODE
        )

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
        remediate(
            conn,
            compliance,
            interfaces,
            dry_run=args.dry_run
        )

        # -------------------------
        # REPORTS
        # -------------------------
        html_file = f"reports/html/report_{timestamp}.html"

        save_json_report(
            device["host"],
            timestamp,
            config_file,
            compliance,
            diff_report,
            EXECUTION_MODE
        )

        generate_html_report(
            compliance,
            diff_report,
            device["host"],
            config_file,
            html_file,
            EXECUTION_MODE
        )

        # -------------------------
        # DISCONNECT + CLOSE DEVICE LOG
        # -------------------------
        conn.disconnect()
        log.info(f"Disconnected from {device['host']}")
        remove_device_handler(device["host"])

    log.info("=" * 60)
    log.info("NetDevOps Framework — Execution Complete")
    log.info("=" * 60)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()