from netmiko import ConnectHandler

device = {
    "device_type": "cisco_xe",
    "host": "devnetsandboxiosxec9k.cisco.com",
    "username": "cyprien.temateu",
    "password": "-RcF2_cHpU5g3S",
}

connection = ConnectHandler(**device)

commands = [
    "show ip interface brief",
    "show version",
    "show run | i hostname",
]

for cmd in commands:
    print(f"\n### {cmd} ###")
    print(connection.send_command(cmd))

connection.disconnect()
