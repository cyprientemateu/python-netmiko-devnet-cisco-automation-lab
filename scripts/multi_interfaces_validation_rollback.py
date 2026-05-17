from netmiko import ConnectHandler
from datetime import datetime

# ========= DEVICE =========
device = {
    "device_type": "cisco_xe",
    "host": "devnetsandboxiosxec9k.cisco.com",
    "username": "cyprien.temateu",
    "password": "_02Flsg2NrA_B",
}

# ========= INTERFACES TO CONFIGURE =========
# routed=True → no switchport + assign IP
# routed=False → L2 interface (no IP)

interfaces_to_configure = [
    {
        "name": "GigabitEthernet1/0/2",
        "description": "Netmiko Automation - LAB1",
        "routed": True,
        "ip": "10.20.30.1",
        "mask": "255.255.255.0",
        "enabled": True
    },
    {
        "name": "GigabitEthernet1/0/3",
        "description": "Netmiko Automation - LAB2",
        "routed": False,
        "enabled": True
    },
    {
        "name": "GigabitEthernet1/0/4",
        "description": "Netmiko Automation - LAB3",
        "routed": True,
        "ip": "10.20.40.1",
        "mask": "255.255.255.0",
        "enabled": True
    }
]


print("Connecting to device...")
conn = ConnectHandler(**device)


# ========= STEP 1 — BACKUP RUNNING CONFIG =========
backup_file = f"backup_{device['host']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
running_cfg = conn.send_command("show running-config")

with open(backup_file, "w") as f:
    f.write(running_cfg)

print(f"\nBackup saved: {backup_file}")


# ========= STEP 2 — PUSH CONFIG =========
print("\nPushing interface configurations...\n")

for iface in interfaces_to_configure:

    commands = [
        f"interface {iface['name']}",
        f"description {iface['description']}",
    ]

    # Routed Layer-3 interface
    if iface.get("routed"):
        commands.append("no switchport")
        commands.append(f"ip address {iface['ip']} {iface['mask']}")

    # Interface state
    commands.append("no shutdown" if iface["enabled"] else "shutdown")
    commands.append("exit")

    print(f"\nConfiguring {iface['name']}...\n")
    print(conn.send_config_set(commands))

conn.save_config()


# ========= STEP 3 — VALIDATION =========
def validate_interface(iface):

    output = conn.send_command(
        "show ip interface brief",
        use_textfsm=True
    )

    if not isinstance(output, list):
        print("[WARN] Parsing failed — raw output returned")
        print(output)
        return False

    # Match interface regardless of field naming
    match = []
    for entry in output:
        name = entry.get("intf") or entry.get("interface") or ""
        if name == iface["name"]:
            match.append(entry)

    if not match:
        print(f"[FAIL] {iface['name']} not found in parsed output")
        return False

    entry = match[0]

    # Normalize key names
    ip_value = (
        entry.get("ipaddr")
        or entry.get("ip_address")
        or entry.get("ipaddr_primary")
        or ""
    )

    status = entry.get("status", "")
    proto = entry.get("proto", "")

    # ===== Routed interface checks =====
    if iface.get("routed"):

        if ip_value != iface["ip"]:
            print(f"[FAIL] {iface['name']} — IP mismatch ({ip_value})")
            return False

        if iface["enabled"]:
            if status != "up" or proto != "up":
                print(f"[FAIL] {iface['name']} — not up/up")
                return False
        else:
            if "administratively" not in status:
                print(f"[FAIL] {iface['name']} — should be shutdown")
                return False

    # ===== Layer-2 interface checks =====
    else:
        if not iface["enabled"] and "administratively" not in status:
            print(f"[FAIL] {iface['name']} — should be shutdown")
            return False

    print(f"[OK] {iface['name']} validated successfully")
    return True


print("\nValidating interfaces...\n")
validation_passed = all(validate_interface(i) for i in interfaces_to_configure)


# ========= STEP 4 — ROLLBACK IF FAILED =========
if not validation_passed:
    print("\n⚠️ Validation failed — restoring backup...\n")

    with open(backup_file, "r") as f:
        backup_config = f.read().splitlines()

    conn.send_config_set(backup_config)

    print("\nRollback completed.")
else:
    print("\n🎉 All interfaces validated successfully — no rollback needed.")

conn.disconnect()
print("\nDone.")
