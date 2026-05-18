import yaml
import os
from dotenv import load_dotenv

load_dotenv()


def load_devices(filepath="inventory/devices.yml"):
    """
    Load device inventory from YAML file.
    Injects credentials from .env automatically.
    Returns a list of device dictionaries ready for Netmiko.
    """
    with open(filepath) as f:
        inventory = yaml.safe_load(f)

    devices = inventory["devices"]

    for device in devices:
        device["username"] = os.getenv("NET_USERNAME")
        device["password"] = os.getenv("NET_PASSWORD")

    return devices


def load_interfaces(filepath="inventory/interfaces.yml"):
    """
    Load interface desired state from YAML file.
    Returns a list of interface dictionaries.
    """
    with open(filepath) as f:
        data = yaml.safe_load(f)

    return data["interfaces"]