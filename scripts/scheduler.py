import os
import sys
import subprocess
import yaml
import schedule
import time
from datetime import datetime
from logger import get_logger

log = get_logger()

# =========================
# PATHS
# =========================
CONFIG_FILE = "config/scheduler_config.yml"
MAIN_SCRIPT = "scripts/main.py"

# =========================
# JOB COUNTER
# Tracks how many compliance runs have executed.
# =========================
job_counter = {"count": 0}


# =========================
# LOAD SCHEDULER CONFIG
# Reads interval, mode and parallel settings
# from config/scheduler_config.yml.
# =========================
def load_config():
    """
    Loads scheduler configuration from YAML file.
    Returns config dict with defaults if file missing.
    """
    defaults = {
        "interval": 60,
        "mode":     "dry-run",
        "parallel": False
    }

    if not os.path.exists(CONFIG_FILE):
        log.warning(
            f"Scheduler config not found at {CONFIG_FILE} — "
            f"using defaults: {defaults}"
        )
        return defaults

    try:
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)
        return config.get("schedule", defaults)
    except Exception as e:
        log.error(f"Failed to load scheduler config — {e}")
        return defaults


# =========================
# COMPLIANCE JOB
# The function that runs on every scheduled interval.
# Calls main.py as a subprocess — same as the Flask dashboard.
# =========================
def run_compliance_job(mode, parallel):
    """
    Executes the full NetDevOps compliance pipeline.
    Called automatically by the scheduler on each interval.
    """
    job_counter["count"] += 1
    job_num   = job_counter["count"]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log.info("=" * 60)
    log.info(f"Scheduled Job #{job_num} — {mode.upper()} | {timestamp}")
    log.info("=" * 60)

    # Build command
    cmd = [sys.executable, MAIN_SCRIPT]

    if mode == "dry-run":
        cmd.append("--dry-run")

    if parallel:
        cmd.append("--parallel")

    try:
        result = subprocess.run(
            cmd,
            capture_output = False,  # stream output live to console
            text           = True,
            encoding       = "utf-8",
            errors         = "replace"
        )

        if result.returncode == 0:
            log.info(f"Job #{job_num} completed successfully ✔")
        else:
            log.error(f"Job #{job_num} completed with errors — check logs")

    except Exception as e:
        log.error(f"Job #{job_num} failed to execute — {e}")

    # Log next run time
    next_run = schedule.next_run()
    if next_run:
        log.info(
            f"Next scheduled run: "
            f"{next_run.strftime('%Y-%m-%d %H:%M:%S')}"
        )


# =========================
# MAIN SCHEDULER LOOP
# =========================
def main():

    log.info("=" * 60)
    log.info("NetDevOps Compliance Scheduler — Starting")
    log.info("=" * 60)

    # -------------------------
    # LOAD CONFIG
    # -------------------------
    config   = load_config()
    interval = config.get("interval", 60)
    mode     = config.get("mode", "dry-run")
    parallel = config.get("parallel", False)

    log.info(f"Interval : every {interval} minute(s)")
    log.info(f"Mode     : {mode.upper()}")
    log.info(f"Parallel : {parallel}")
    log.info("=" * 60)

    # -------------------------
    # RUN IMMEDIATELY ON START
    # -------------------------
    log.info("Running initial compliance job on startup...")
    run_compliance_job(mode, parallel)

    # -------------------------
    # SCHEDULE RECURRING JOBS
    # -------------------------
    schedule.every(interval).minutes.do(
        run_compliance_job, mode=mode, parallel=parallel
    )

    log.info(f"Scheduler active — running every {interval} minute(s)")
    log.info("Press CTRL+C to stop")

    # -------------------------
    # KEEP RUNNING
    # -------------------------
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # check every 30 seconds

    except KeyboardInterrupt:
        log.info("=" * 60)
        log.info(
            f"Scheduler stopped — "
            f"{job_counter['count']} job(s) completed"
        )
        log.info("=" * 60)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()