import contextvars
from typing import Any, Dict


_context_vars: Dict[str, contextvars.ContextVar] = {}


def set_vars(**kwargs):
    global _context_vars

    for key, value in kwargs.items():
        if key not in _context_vars:
            context_var = contextvars.ContextVar(key)
            context_var.set(value)
            _context_vars[key] = context_var
        _context_vars[key].set(value)


def get_var(key: str) -> Any:
    global _context_vars

    if key not in _context_vars:
        return None
    return _context_vars[key].get(None)


def set_trace(value: str):
    set_vars(trace=value)
