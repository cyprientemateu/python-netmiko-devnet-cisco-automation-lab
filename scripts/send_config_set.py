from netmiko import ConnectHandler

# ====== DEVICE DETAILS ======
device = {
    "device_type": "cisco_xe",
    "host": "devnetsandboxiosxec9k.cisco.com",
    "username": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD",
}

# ====== INTERFACE CONFIG INPUTS ======
interface_name = "GigabitEthernet1/0/2"
description = "Configured via Netmiko Automation"
ip_address = "10.20.30.1"
subnet_mask = "255.255.255.0"
enable_interface = True   # set to False if you want shutdown

# ====== CONNECT ======
connection = ConnectHandler(**device)

# =========================
# 1. CONFIG PUSH
# =========================
config_commands = [
    f"interface {interface_name}", 
    # Convert to Layer-3 routed interface
    "no switchport",
    f"description {description}",
]

# Add IP only if provided
if ip_address and subnet_mask:
    config_commands.append(f"ip address {ip_address} {subnet_mask}")

# Enable / disable interface
config_commands.append("no shutdown" if enable_interface else "shutdown")

config_commands.append("exit")

print("\nPushing configuration...\n")
output = connection.send_config_set(config_commands)
print(output)

# =========================
# 2. SAVE CONFIG
# =========================
print("\nSaving configuration...\n")
save_output = connection.send_command("write memory")
print(save_output)

# =========================
# 3. 🔍 VERIFICATION 
# =========================
print("\nVerifying configuration...\n")

verify_output = connection.send_command(
    f"show running-config interface {interface_name}"
)

print(verify_output)

# Simple validation check
if ip_address in verify_output and description in verify_output:
    print("\n✅ VERIFICATION SUCCESS: Interface configured correctly")
else:
    print("\n❌ VERIFICATION FAILED: Mismatch detected")

# =========================
# 4. DISCONNECT
# =========================
connection.disconnect()
print("\nInterface configuration completed.")
