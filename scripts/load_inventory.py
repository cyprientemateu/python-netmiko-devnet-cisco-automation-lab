import yaml
import os
from dotenv import load_dotenv

load_dotenv()

with open("inventory/devices.yml") as f:
    inventory = yaml.safe_load(f)

devices = inventory["devices"]

for device in devices:

    device["username"] = os.getenv("NET_USERNAME")
    device["password"] = os.getenv("NET_PASSWORD")

print(devices)