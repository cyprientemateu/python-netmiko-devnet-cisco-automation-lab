from netmiko import ConnectHandler
from datetime import datetime
import json

# ========= DEVICE =========
device = {
    "device_type": "cisco_xe",
    "host": "devnetsandboxiosxec9k.cisco.com",
    "username": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD",
}

conn = ConnectHandler(**device)

# ========= MODE FLAGS =========
DRY_RUN = False  # change to True to simulate only

# ========= INTERFACES =========
interfaces_to_configure = [
    {
        "name": "GigabitEthernet1/0/2",
        "description": "LAB1",
        "routed": True,
        "ip": "10.20.30.1",
        "mask": "255.255.255.0",
        "enabled": True
    },
    {
        "name": "GigabitEthernet1/0/3",
        "description": "LAB2",
        "routed": False,
        "enabled": True
    },
    {
        "name": "GigabitEthernet1/0/4",
        "description": "LAB3",
        "routed": True,
        "ip": "10.20.40.1",
        "mask": "255.255.255.0",
        "enabled": True
    }
]

# ========= BACKUP (LOCAL + DEVICE) =========
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = f"backup_{device['host']}_{timestamp}.txt"

running_cfg = conn.send_command("show running-config")

with open(backup_file, "w") as f:
    f.write(running_cfg)

# device backup (safe method)
conn.save_config()  # saves to startup-config

print(f"\nBackup saved locally: {backup_file}")
print("Backup saved on device: startup-config updated\n")


# ========= DRIFT DETECTION =========
print("\nChecking drift...\n")
current_state = conn.send_command("show ip interface brief", use_textfsm=True)

drift_interfaces = []
for iface in interfaces_to_configure:
    found = False
    for entry in current_state:
        name = entry.get("intf") or entry.get("interface")
        if name == iface["name"]:
            found = True
    if not found:
        drift_interfaces.append(iface["name"])

if drift_interfaces:
    print("⚠️ Drift detected:", drift_interfaces)


# ========= DRY RUN =========
if DRY_RUN:
    print("\n🧪 DRY RUN MODE — No changes applied\n")
    for iface in interfaces_to_configure:
        print(f"Would configure: {iface['name']}")
    conn.disconnect()
    exit()


# ========= CONFIG PUSH =========
print("\nPushing configuration...\n")

results = []

for iface in interfaces_to_configure:

    print(f"\nConfiguring {iface['name']}...\n")

    commands = [
        f"interface {iface['name']}",
        f"description {iface['description']}",
    ]

    # idempotent check (simple)
    show_int = conn.send_command(
        f"show run interface {iface['name']}"
    )

    if iface["description"] in show_int:
        print("✔ Already configured (idempotent skip logic)")
        results.append({"interface": iface["name"], "status": "SKIPPED"})
        continue

    # routed
    if iface.get("routed"):
        commands.append("no switchport")
        commands.append(f"ip address {iface['ip']} {iface['mask']}")

    commands.append("no shutdown" if iface["enabled"] else "shutdown")
    commands.append("exit")

    output = conn.send_config_set(commands)
    print(output)

    results.append({"interface": iface["name"], "status": "CONFIGURED"})


# ========= SAVE CONFIG =========
conn.save_config()


# ========= VALIDATION =========
print("\nValidating interfaces...\n")

validation_results = []

for iface in interfaces_to_configure:
    output = conn.send_command(f"show ip interface brief")

    status = "UNKNOWN"
    if iface["name"] in output:
        status = "PRESENT"

    validation_results.append({
        "interface": iface["name"],
        "status": status
    })

    print(f"[{status}] {iface['name']}")


# ========= REPORT FILE =========
report = {
    "timestamp": timestamp,
    "device": device["host"],
    "drift": drift_interfaces,
    "results": results,
    "validation": validation_results
}

report_file = f"report_{timestamp}.json"

with open(report_file, "w") as f:
    json.dump(report, f, indent=4)

print(f"\n📊 Report generated: {report_file}")


conn.disconnect()
print("\nDone.")