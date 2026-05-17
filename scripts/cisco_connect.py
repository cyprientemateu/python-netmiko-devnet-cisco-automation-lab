from netmiko import ConnectHandler
# replace with your sandbox details
device = {
    "device_type": "cisco_xe",
    "host": "devnetsandboxiosxec9k.cisco.com",  
    "username": "cyprien.temateu",
    "password": "-RcF2_cHpU5g3S",
}

connection = ConnectHandler(**device)

output = connection.send_command("show ip interface brief")
print(output)

connection.disconnect()
