from jinja2 import Environment, FileSystemLoader

# =========================
# LOAD TEMPLATE
# =========================
env = Environment(
    loader=FileSystemLoader("templates")
)

template = env.get_template("interface.j2")

# =========================
# INTERFACE VARIABLES
# =========================
interfaces = [

    {
        "interface": "GigabitEthernet1/0/2",
        "description": "Jinja2 LAB1",
        "routed": True,
        "ip": "10.10.10.1",
        "mask": "255.255.255.0",
        "enabled": True
    },

    {
        "interface": "GigabitEthernet1/0/3",
        "description": "Jinja2 LAB2",
        "routed": False,
        "enabled": False
    },

    {
        "interface": "GigabitEthernet1/0/4",
        "description": "Jinja2 LAB3",
        "routed": True,
        "ip": "10.20.40.1",
        "mask": "255.255.255.0",
        "enabled": True
    }
]

# =========================
# GENERATE CONFIGS
# =========================
for interface in interfaces:

    config = template.render(interface)

    print("\n====================")
    print(config)