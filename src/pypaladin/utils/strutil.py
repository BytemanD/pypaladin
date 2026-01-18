import ipaddress
from typing import Tuple


_TRUE_VALUES = ("true", "1", "on", "yes", "y", "ok", "enable")
_FALSE_VALUES = ("false", "0", "off", "no", "n", "nok", "disable")
V4 = "v4"


def str2bool(value: str, strict=False) -> bool:
    if strict and value.lower() not in _TRUE_VALUES + _FALSE_VALUES:
        raise ValueError("Invalid value for boolean")
    return value.lower() in _TRUE_VALUES


def is_valid_ip(ip: str) -> Tuple[bool, str]:
    try:
        ipaddress.IPv4Address(ip)
        return True, "v4"
    except ipaddress.AddressValueError:
        pass

    try:
        ipaddress.IPv6Address(ip)
        return True, "v6"
    except ipaddress.AddressValueError:
        pass
    return False, None
