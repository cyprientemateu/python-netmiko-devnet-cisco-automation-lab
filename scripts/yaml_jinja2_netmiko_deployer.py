from netmiko import ConnectHandler
from jinja2 import Environment, FileSystemLoader
from load_inventory import load_devices, load_interfaces

# =========================
# LOAD INVENTORY
# =========================
devices    = load_devices()
interfaces = load_interfaces()

# =========================
# LOAD JINJA2 TEMPLATE
# =========================
env      = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("interface.j2")

# =========================
# CONNECT + PUSH PER DEVICE
# =========================
for device in devices:

    print(f"\n{'='*50}")
    print(f"Connecting to {device['host']}...")
    print(f"{'='*50}")

    conn = ConnectHandler(**device)

    # -------------------------
    # PUSH CONFIG PER INTERFACE
    # -------------------------
    for intf in interfaces:

        print(f"\n--- Generating config: {intf['interface']} ---")

        # Render Jinja2 template with interface data
        config = template.render(intf)

        print(config)

        # Strip blank lines before sending
        commands = [
            line for line in config.splitlines()
            if line.strip()
        ]

        output = conn.send_config_set(commands)
        print(output)

    # -------------------------
    # SAVE CONFIGURATION
    # -------------------------
    print("\nSaving configuration...")
    save_output = conn.send_command("write memory")
    print(save_output)

    conn.disconnect()

    print(f"\n✔ DONE — {device['host']}")

print("\n✔ ALL DEVICES COMPLETE")