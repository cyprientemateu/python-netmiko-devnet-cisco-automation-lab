import argparse
import os
from datetime import datetime

from load_inventory    import load_devices, load_interfaces
from logger            import get_logger, add_device_handler, remove_device_handler
from core.validator    import validate_inventory
from core.orchestrator import process_device, run_parallel

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
parser.add_argument(
    "--parallel",
    action="store_true",
    help="Process all devices simultaneously"
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
    # -------------------------
    timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    execution_id = f"EXEC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    log = get_logger(execution_id=execution_id)

    mode_label = "PARALLEL" if args.parallel else "SEQUENTIAL"

    log.info("=" * 60)
    log.info(f"NetDevOps Framework — {EXECUTION_MODE} | {mode_label}")
    log.info(f"Execution ID : {execution_id}")
    log.info(f"Devices      : {len(devices)}")
    log.info("=" * 60)

    # -------------------------
    # SCHEMA VALIDATION
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

    # -------------------------
    # EXECUTION — SEQUENTIAL OR PARALLEL
    # -------------------------
    if args.parallel:

        run_parallel(
            devices,
            interfaces,
            timestamp,
            EXECUTION_MODE,
            args.dry_run
        )

    else:

        for device in devices:
            device_id = device.get("label", device["host"])
            log.info(f"Processing device: {device['host']} (label: {device_id})")
            process_device(
                device,
                interfaces,
                timestamp,
                EXECUTION_MODE,
                args.dry_run
            )

    log.info("=" * 60)
    log.info("NetDevOps Framework — Execution Complete")
    log.info("=" * 60)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()