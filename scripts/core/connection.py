from netmiko import ConnectHandler
from logger import get_logger

log = get_logger()


def connect(device):
    """
    Establishes an SSH connection to a network device using Netmiko.
    Strips any non-Netmiko fields (e.g. label) before passing
    the device dict to ConnectHandler.
    Raises exception on failure so main.py can skip the device cleanly.
    """
    log.info(f"Connecting to {device['host']}...")
    try:
        # Filter to Netmiko-accepted fields only
        netmiko_params = {
            k: v for k, v in device.items()
            if k not in ("label", "restconf_port")
        }

        # Add timing parameters to handle prompt detection
        # on DevNet sandbox devices with non-standard prompts
        netmiko_params["global_delay_factor"] = 2
        netmiko_params["fast_cli"]            = False
        netmiko_params["conn_timeout"]        = 15

        conn = ConnectHandler(**netmiko_params)
        log.info(f"Connection established — {device['host']}")
        return conn
    except Exception as e:
        log.error(f"Connection failed — {device['host']} — {e}")
        raise


def get_running_config(conn):
    """
    Collects the full running configuration from the connected device.
    Returns the config as a raw string.
    """
    log.info("Collecting running config...")
    return conn.send_command("show running-config")