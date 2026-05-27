import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# =========================
# WINDOWS UTF-8 FIX
# Forces console to UTF-8 so special characters (→, ✔, etc.)
# render correctly in PowerShell / Windows Terminal.
# =========================
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# =========================
# CREATE LOGS FOLDER
# =========================
os.makedirs("logs", exist_ok=True)

# =========================
# LOG FORMAT
# Includes execution_id so every line is traceable to one run.
# =========================
LOG_FORMAT  = "%(asctime)s | %(levelname)-8s | [%(execution_id)s] | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# =========================
# EXECUTION ID FILTER
# Injects execution_id into every log record so all messages
# from one run share the same traceable ID.
# =========================
class ExecutionIDFilter(logging.Filter):

    def __init__(self, execution_id="STARTUP"):
        super().__init__()
        self.execution_id = execution_id

    def filter(self, record):
        record.execution_id = self.execution_id
        return True


# =========================
# GET LOGGER
# Returns the configured singleton logger.
# If already initialized, updates the execution_id on the
# existing filter so all modules stay in sync with main.py.
#
# Usage:
#   from logger import get_logger
#   log = get_logger()                         # core modules
#   log = get_logger(execution_id=exec_id)     # main.py
# =========================
def get_logger(name="netdevops", execution_id="STARTUP"):

    logger = logging.getLogger(name)

    if logger.handlers:
        # Logger already configured — update execution_id only
        for f in logger.filters:
            if isinstance(f, ExecutionIDFilter):
                f.execution_id = execution_id
        return logger

    logger.setLevel(logging.DEBUG)

    # -------------------------
    # EXECUTION ID FILTER
    # -------------------------
    exec_filter = ExecutionIDFilter(execution_id)
    logger.addFilter(exec_filter)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # -------------------------
    # CONSOLE HANDLER
    # -------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # -------------------------
    # ROTATING FILE HANDLER — main log
    # Max 5MB per file, keeps last 5 rotated files.
    # logs/netdevops.log
    # logs/netdevops.log.1
    # logs/netdevops.log.2  ... up to .5
    # -------------------------
    file_handler = RotatingFileHandler(
        "logs/netdevops.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # -------------------------
    # ATTACH HANDLERS
    # -------------------------
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# =========================
# ADD DEVICE HANDLER
# Adds a per-device rotating log file when a device
# starts being processed.
#
# logs/{device_host}.log
#
# Usage in main.py:
#   add_device_handler(device["host"])
# =========================
def add_device_handler(device_host):

    logger    = logging.getLogger("netdevops")
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # Avoid duplicate handlers if called twice for same device
    for h in logger.handlers:
        if getattr(h, "_device_host", None) == device_host:
            return

    device_handler = RotatingFileHandler(
        f"logs/{device_host}.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    device_handler.setLevel(logging.DEBUG)
    device_handler.setFormatter(formatter)
    device_handler._device_host = device_host  # tag for identification

    logger.addHandler(device_handler)


# =========================
# REMOVE DEVICE HANDLER
# Closes and removes the per-device log handler after
# the device has been fully processed.
#
# Usage in main.py:
#   remove_device_handler(device["host"])
# =========================
def remove_device_handler(device_host):

    logger = logging.getLogger("netdevops")

    handlers_to_remove = [
        h for h in logger.handlers
        if getattr(h, "_device_host", None) == device_host
    ]

    for h in handlers_to_remove:
        h.close()
        logger.removeHandler(h)