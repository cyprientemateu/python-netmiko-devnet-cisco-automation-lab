import ipaddress
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator, ValidationError
from logger import get_logger

log = get_logger()


# =========================
# DEVICE MODEL
# Validates each entry in inventory/devices.yml.
# Credentials (username/password) are injected by
# load_inventory.py from .env — validated here to catch
# missing .env configuration early.
# =========================
class DeviceModel(BaseModel):

    host:          str
    device_type:   str
    username:      Optional[str] = None
    password:      Optional[str] = None
    label:         Optional[str] = None
    restconf_port: Optional[int] = 443

    @model_validator(mode="after")
    def check_credentials(self):
        if not self.username:
            raise ValueError(
                "username is missing — check .env NET_USERNAME"
            )
        if not self.password:
            raise ValueError(
                "password is missing — check .env NET_PASSWORD"
            )
        return self


# =========================
# INTERFACE MODEL
# Validates each entry in inventory/interfaces.yml.
# Enforces that routed interfaces always have ip and mask.
# Validates ip and mask are valid IPv4 format.
# =========================
class InterfaceModel(BaseModel):

    interface:   str
    description: str
    routed:      bool = False
    enabled:     bool = True
    ip:          Optional[str] = None
    mask:        Optional[str] = None

    @field_validator("ip", "mask")
    @classmethod
    def validate_ip_format(cls, v):
        """Validates that ip and mask are valid IPv4 addresses."""
        if v is not None:
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError(f"'{v}' is not a valid IPv4 address")
        return v

    @model_validator(mode="after")
    def check_routed_fields(self):
        """
        Enforces that routed interfaces always declare
        both ip and mask. Catches missing IP config before
        any connection is made.
        """
        if self.routed:
            if not self.ip:
                raise ValueError(
                    "ip is required when routed is True"
                )
            if not self.mask:
                raise ValueError(
                    "mask is required when routed is True"
                )
        return self


# =========================
# VALIDATE INVENTORY
# Validates all devices and interfaces against their models.
# Collects ALL errors before returning — does not fail on
# the first error — so the operator sees the full picture.
#
# Returns:
#   errors (list): empty if all valid, populated if any fail
#
# Usage in main.py:
#   from core.validator import validate_inventory
#   errors = validate_inventory(devices, interfaces)
#   if errors:
#       # log and abort
# =========================
def validate_inventory(devices, interfaces):

    errors = []

    # -------------------------
    # VALIDATE DEVICES
    # -------------------------
    for i, device in enumerate(devices):
        try:
            DeviceModel(**device)
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                prefix = f"devices[{i}].{field}" if field else f"devices[{i}]"
                errors.append(f"{prefix}: {error['msg']}")

    # -------------------------
    # VALIDATE INTERFACES
    # -------------------------
    for i, intf in enumerate(interfaces):
        try:
            InterfaceModel(**intf)
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                prefix = f"interfaces[{i}].{field}" if field else f"interfaces[{i}]"
                errors.append(f"{prefix}: {error['msg']}")

    return errors