from logger import get_logger

log = get_logger()


def save_backup(actual_config, device_host, timestamp):
    """
    Saves the collected running config to a timestamped file
    in the backups/ directory.
    Raises exception on failure so main.py can skip the device cleanly.
    """
    backup_file = f"backups/backup_{device_host}_{timestamp}.txt"
    try:
        with open(backup_file, "w") as f:
            f.write(actual_config)
        log.info(f"Backup saved — {backup_file}")
        return backup_file
    except Exception as e:
        log.error(f"Backup failed — {device_host} — {e}")
        raise