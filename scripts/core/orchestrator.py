import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from logger          import get_logger, add_device_handler, remove_device_handler
from core.connection  import connect, get_running_config
from core.backup      import save_backup
from core.rendering   import render_and_save_configs
from core.compliance  import diff_configs, compliance_check
from core.remediation import remediate
from core.reporting   import save_json_report, generate_html_report

log = get_logger()

# Thread lock for safe handler management in parallel mode
_handler_lock = threading.Lock()


# =========================
# PROCESS DEVICE
# Full pipeline for a single device.
# Called by both sequential loop and parallel executor.
# All log messages prefixed with [host] so parallel
# output remains readable when interleaved.
# =========================
def process_device(device, interfaces, timestamp, execution_mode, dry_run):
    """
    Runs the full NetDevOps pipeline for one device:
    connect → backup → render → diff → compliance → remediate → report

    Designed to be thread-safe for parallel execution.
    Per-device log handler is opened and closed here.
    """
    host      = device["host"]
    device_id = device.get("label", host)

    # -------------------------
    # PER-DEVICE LOG HANDLER
    # Uses device_id so same-host devices get separate log files
    # -------------------------
    with _handler_lock:
        add_device_handler(device_id)

    try:

        # -------------------------
        # CONNECT
        # -------------------------
        try:
            conn = connect(device)
        except Exception:
            log.error(f"[{device_id}] Skipping — could not connect")
            return

        # -------------------------
        # BACKUP
        # -------------------------
        try:
            actual = get_running_config(conn)
            save_backup(actual, device_id, timestamp)
        except Exception as e:
            log.error(f"[{device_id}] Backup failed — {e}")
            conn.disconnect()
            return

        # -------------------------
        # RENDER + SAVE CONFIGS
        # -------------------------
        config_file = render_and_save_configs(
            interfaces, device_id, timestamp, execution_mode
        )

        # -------------------------
        # DIFF ENGINE
        # -------------------------
        log.info(f"[{device_id}] Running diff engine...")
        diff_report = diff_configs(interfaces, actual)

        # -------------------------
        # COMPLIANCE CHECK
        # -------------------------
        log.info(f"[{device_id}] Running compliance check...")
        compliance = compliance_check(diff_report)

        for intf, result in compliance.items():
            if result == "COMPLIANT":
                log.info(f"[{device_id}] [OK]    {intf} → {result}")
            else:
                log.warning(f"[{device_id}] [DRIFT] {intf} → {result}")

        # -------------------------
        # REMEDIATION
        # -------------------------
        log.info(f"[{device_id}] Running remediation engine...")
        remediate(conn, compliance, interfaces, dry_run=dry_run)

        # -------------------------
        # REPORTS
        # -------------------------
        html_file = f"reports/html/report_{device_id}_{timestamp}.html"

        save_json_report(
            device_id, timestamp, config_file,
            compliance, diff_report, execution_mode
        )

        generate_html_report(
            compliance, diff_report, device_id,
            config_file, html_file, execution_mode
        )

        # -------------------------
        # DISCONNECT
        # -------------------------
        conn.disconnect()
        log.info(f"[{device_id}] Processing complete ✔")

    finally:
        with _handler_lock:
            remove_device_handler(device_id)


# =========================
# RUN PARALLEL
# Executes process_device() for all devices concurrently
# using ThreadPoolExecutor.
# max_workers = number of devices so all run simultaneously.
# =========================
def run_parallel(devices, interfaces, timestamp, execution_mode, dry_run):
    """
    Runs the full pipeline for all devices simultaneously.
    Each device runs in its own thread.
    Results are collected as they complete.
    """
    log.info(f"Running PARALLEL mode — {len(devices)} device(s)")

    with ThreadPoolExecutor(max_workers=len(devices)) as executor:

        futures = {
            executor.submit(
                process_device,
                device,
                interfaces,
                timestamp,
                execution_mode,
                dry_run
            ): device["host"]
            for device in devices
        }

        for future in as_completed(futures):
            host = futures[future]
            try:
                future.result()
            except Exception as e:
                log.error(f"[{host}] Unhandled error — {e}")