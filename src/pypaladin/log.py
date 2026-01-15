import sys
from typing import Dict, List, Optional

from loguru import logger
from pydantic import BaseModel

from pypaladin import context

DEFAULT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}:{line}</cyan> <level>[{extra[context]}]</level> - <level>{message}</level>"
)


class LogConfig(BaseModel):
    level: str = "INFO"
    file: Optional[str] = None
    format: str = DEFAULT_FORMAT
    colorize: Optional[bool] = None
    custom_extra: List[str] = []


def _patcher(record: Dict, extra_keys: List[str] = []):
    ctx_value = " ".join([str(context.get_var(x) or "-") for x in extra_keys])
    record.update(extra={"context": ctx_value or "-"})


def setup_logger(config: LogConfig):
    """Setup logging configuration."""
    logger.remove()
    kwargs = {}
    if config.format:
        kwargs["format"] = config.format
    if config.colorize:
        kwargs["colorize"] = config.colorize
    logger.add(
        config.file if config.file else sys.stdout,
        level=config.level.upper(),
        **kwargs,
    )
    logger.configure(
        extra={"context": "-"},
        patcher=lambda record: _patcher(record, ["trace"] + config.custom_extra),  # type: ignore
    )
