import logging
import os
import sys

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


def get_logger(name="netdevops"):
    """
    Returns a configured logger that writes to:
    - Console (so the user still sees live output)
    - logs/netdevops.log (persistent audit file)

    Usage in any script:
        from logger import get_logger
        log = get_logger()
        log.info("Connecting to device...")
        log.warning("Drift detected on GigabitEthernet1/0/2")
        log.error("SSH authentication failed")
    """

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # -------------------------
    # LOG FORMAT
    # -------------------------
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # -------------------------
    # CONSOLE HANDLER
    # -------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # -------------------------
    # FILE HANDLER
    # -------------------------
    file_handler = logging.FileHandler("logs/netdevops.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # -------------------------
    # ATTACH HANDLERS
    # -------------------------
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger