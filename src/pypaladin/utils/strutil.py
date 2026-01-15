_TRUE_VALUES = ("true", "1", "on", "yes", "y", "ok", "enable")
_FALSE_VALUES = ("false", "0", "off", "no", "n", "nok", "disable")


def str2bool(value: str, strict=False) -> bool:
    if strict and value.lower() not in _TRUE_VALUES + _FALSE_VALUES:
        raise ValueError("Invalid value for boolean")
    return value.lower() in _TRUE_VALUES
