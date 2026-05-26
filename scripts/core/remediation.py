from logger import get_logger

log = get_logger()


def remediate(conn, compliance, interfaces, dry_run=False):
    """
    Pushes the full desired config to any interface showing DRIFT.

    In dry_run mode, remediation is skipped entirely —
    no changes are pushed to the device.

    Pushes per DRIFT interface:
    - description
    - routed/switchport mode
    - ip address and mask
    - shutdown state
    """
    if dry_run:
        log.warning("DRY-RUN MODE — remediation skipped, no changes pushed")
        return

    any_drift = any(
        status == "DRIFT"
        for status in compliance.values()
    )

    if not any_drift:
        log.info("All interfaces COMPLIANT — no remediation needed")
        return

    for intf in interfaces:

        name   = intf["interface"]
        status = compliance.get(name)

        if status == "DRIFT":

            log.warning(f"Remediating {name}...")

            try:
                cfg = [f"interface {name}"]
                cfg.append(f"description {intf['description']}")

                if intf.get("routed"):
                    cfg.append("no switchport")
                    cfg.append(f"ip address {intf['ip']} {intf['mask']}")
                else:
                    cfg.append("switchport")

                if intf.get("enabled"):
                    cfg.append("no shutdown")
                else:
                    cfg.append("shutdown")

                conn.send_config_set(cfg)
                log.info(f"Remediation successful — {name}")

            except Exception as e:
                log.error(f"Remediation failed — {name} — {e}")