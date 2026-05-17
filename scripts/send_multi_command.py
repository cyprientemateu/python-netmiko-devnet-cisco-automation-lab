from netmiko import ConnectHandler

device = {
    "device_type": "cisco_xe",
    "host": "devnetsandboxiosxec9k.cisco.com",
    "username": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD",
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
