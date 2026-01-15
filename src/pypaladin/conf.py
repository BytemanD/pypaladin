from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from pypaladin import log
from pypaladin.log import LogConfig


class HTTPClientConfig(BaseModel):
    timeout: int = 60
    retries: int = 0


class BaseAppConfig(BaseSettings):
    """Base App Configuration"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )

    httpclient: HTTPClientConfig = HTTPClientConfig()
    log: LogConfig = LogConfig()

    def __init__(self):
        super().__init__()

    @classmethod
    def setup(cls):
        global _BASE_CONF

        conf = cls()
        log.setup_logger(conf.log)

        _BASE_CONF = conf


_BASE_CONF = BaseAppConfig()
