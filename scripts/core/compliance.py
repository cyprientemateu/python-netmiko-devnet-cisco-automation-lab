import difflib
from logger import get_logger

log = get_logger()


def build_expected_lines(intf):
    """
    Builds the list of sub-commands we expect to find
    inside the interface block on the device.

    Rules:
    - No leading spaces: we normalize both sides before comparing.
    - No interface header line: extract_interface_block strips it.
    - No 'no shutdown': Cisco IOS omits this from running-config
      when an interface is up — it is the default and invisible.
      We only check for 'shutdown' when the interface should be down.
    """
    lines = []
    lines.append(f"description {intf['description']}")

    if intf.get("routed"):
        lines.append("no switchport")
        lines.append(f"ip address {intf['ip']} {intf['mask']}")

    if not intf.get("enabled"):
        lines.append("shutdown")

    return lines


def extract_interface_block(running_config, interface_name):
    """
    Extracts sub-command lines for a specific interface
    from the full running config.

    - Skips the interface header line itself.
    - Strips leading/trailing whitespace from each line
      so comparison with expected lines is normalized.
    - Stops at the next interface block or '!' marker.
    """
    lines    = running_config.splitlines()
    block    = []
    in_block = False

    for line in lines:

        if line.strip().lower() == f"interface {interface_name.lower()}":
            in_block = True
            continue

        if in_block:
            if line.startswith("interface ") or line.strip() == "!":
                break
            if line.strip():
                block.append(line.strip())

    return block


def diff_configs(interfaces, running_config):
    """
    For each interface, checks whether all expected lines
    are present in the actual device block.

    Uses subset logic — not exact match — because:
    - Cisco adds lines we don't control (negotiation auto,
      spanning-tree, etc.)
    - An exact diff would always show DRIFT due to those extras.
    - We only care that OUR desired lines are present.
    """
    diff_report = {}

    for intf in interfaces:

        name     = intf["interface"]
        expected = build_expected_lines(intf)
        actual   = extract_interface_block(running_config, name)

        missing = [
            line for line in expected
            if line not in actual
        ]

        diff = list(
            difflib.unified_diff(
                expected,
                actual,
                fromfile="desired",
                tofile="actual",
                lineterm=""
            )
        )

        diff_report[name] = {
            "expected": expected,
            "actual":   actual,
            "missing":  missing,
            "diff":     diff
        }

    return diff_report


def compliance_check(diff_report):
    """
    Classifies each interface as COMPLIANT or DRIFT
    based on whether any expected lines are missing.
    """
    results = {}

    for intf, data in diff_report.items():
        if not data["missing"]:
            results[intf] = "COMPLIANT"
        else:
            results[intf] = "DRIFT"

    return results