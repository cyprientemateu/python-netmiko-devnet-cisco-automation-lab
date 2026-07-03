import requests
import urllib3
from logger import get_logger

log = get_logger()

# Suppress SSL warnings for DevNet sandbox self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =========================
# RESTCONF HEADERS
# Standard headers required for RESTCONF JSON responses.
# =========================
RESTCONF_HEADERS = {
    "Accept":       "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}

# =========================
# RESTCONF INTERFACE ENDPOINT
# IOS-XE YANG model for interface configuration.
# Returns all interface config including description,
# IP address, and enabled state.
# =========================
RESTCONF_INTF_PATH = (
    "/restconf/data/ietf-interfaces:interfaces"
)


# =========================
# GET RESTCONF INTERFACES
# Retrieves interface state from the device via RESTCONF.
# Returns parsed JSON dict or None on failure.
#
# Args:
#   host          : device hostname
#   username      : device username
#   password      : device password
#   port          : RESTCONF port (default 443)
#   device_id     : label for log messages
# =========================
def get_restconf_interfaces(
    host, username, password, port=443, device_id=None
):
    """
    Retrieves interface data from the device via RESTCONF GET.
    Uses HTTPS with SSL verification disabled for DevNet sandbox.
    Returns the parsed JSON response or None on failure.
    """
    label = device_id or host
    url   = f"https://{host}:{port}{RESTCONF_INTF_PATH}"

    log.info(f"[{label}] Running RESTCONF compliance check...")

    try:
        response = requests.get(
            url,
            auth=(username, password),
            headers=RESTCONF_HEADERS,
            verify=False,
            timeout=10
        )

        if response.status_code == 200:
            log.info(f"[{label}] RESTCONF GET successful — {url}")
            return response.json()

        else:
            log.error(
                f"[{label}] RESTCONF GET failed — "
                f"HTTP {response.status_code} — {url}"
            )
            return None

    except requests.exceptions.ConnectionError as e:
        log.error(f"[{label}] RESTCONF connection error — {e}")
        return None
    except requests.exceptions.Timeout:
        log.error(f"[{label}] RESTCONF request timed out — {url}")
        return None
    except Exception as e:
        log.error(f"[{label}] RESTCONF unexpected error — {e}")
        return None


# =========================
# PARSE RESTCONF INTERFACES
# Converts the raw RESTCONF JSON response into a flat dict
# keyed by interface name for easy comparison.
#
# Returns:
#   {
#     "GigabitEthernet1/0/2": {
#       "description": "YAML LAB1",
#       "enabled": True,
#       "ip": "10.10.10.1",
#       "mask": "255.255.255.0"
#     },
#     ...
#   }
# =========================
def parse_restconf_interfaces(data):
    """
    Parses the RESTCONF ietf-interfaces response into a flat dict.
    Extracts description, enabled state, and IP address per interface.
    """
    parsed = {}

    if not data:
        return parsed

    interfaces = data.get(
        "ietf-interfaces:interfaces", {}
    ).get("interface", [])

    for intf in interfaces:

        name        = intf.get("name", "")
        description = intf.get("description", "")
        enabled     = intf.get("enabled", True)

        # Extract IPv4 address if present
        ip   = None
        mask = None

        ipv4 = (
            intf
            .get("ietf-ip:ipv4", {})
            .get("address", [])
        )

        if ipv4:
            ip   = ipv4[0].get("ip")
            mask = ipv4[0].get("netmask")

        parsed[name] = {
            "description": description,
            "enabled":     enabled,
            "ip":          ip,
            "mask":        mask
        }

    return parsed


# =========================
# RESTCONF COMPLIANCE CHECK
# Compares desired interface state (from interfaces.yml)
# against actual state retrieved via RESTCONF.
#
# Returns a dict of compliance results per interface:
#   { "GigabitEthernet1/0/2": "COMPLIANT" | "DRIFT" | "NOT_FOUND" }
# =========================
def restconf_compliance_check(interfaces, restconf_data, device_id=None):
    """
    Compares desired state from interfaces.yml against
    actual state from RESTCONF response.

    Checks per interface:
    - description matches
    - enabled state matches
    - ip address matches (if routed)
    - mask matches (if routed)

    Returns compliance result per interface.
    """
    label   = device_id or "device"
    parsed  = parse_restconf_interfaces(restconf_data)
    results = {}

    for intf in interfaces:

        name   = intf["interface"]
        issues = []

        if name not in parsed:
            log.warning(
                f"[{label}] RESTCONF [{name}] NOT FOUND in response"
            )
            results[name] = "NOT_FOUND"
            continue

        actual = parsed[name]

        # Check description
        if intf.get("description") != actual.get("description"):
            issues.append(
                f"description: "
                f"expected '{intf.get('description')}' "
                f"got '{actual.get('description')}'"
            )

        # Check enabled state
        if intf.get("enabled") != actual.get("enabled"):
            issues.append(
                f"enabled: "
                f"expected '{intf.get('enabled')}' "
                f"got '{actual.get('enabled')}'"
            )

        # Check IP and mask for routed interfaces
        if intf.get("routed"):
            if intf.get("ip") != actual.get("ip"):
                issues.append(
                    f"ip: "
                    f"expected '{intf.get('ip')}' "
                    f"got '{actual.get('ip')}'"
                )
            if intf.get("mask") != actual.get("mask"):
                issues.append(
                    f"mask: "
                    f"expected '{intf.get('mask')}' "
                    f"got '{actual.get('mask')}'"
                )

        if issues:
            results[name] = "DRIFT"
            for issue in issues:
                log.warning(f"[{label}] RESTCONF [{name}] DRIFT — {issue}")
        else:
            results[name] = "COMPLIANT"
            log.info(f"[{label}] RESTCONF [{name}] → COMPLIANT")

    return results