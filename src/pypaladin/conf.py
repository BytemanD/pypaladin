from pydantic_settings import BaseSettings, SettingsConfigDict

from pypaladin import log
from pypaladin.httpclient import HTTPClientConfig
from pypaladin.log import LogConfig


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

    def setup(self):
        global _DEFAULT_CONF
        log.setup_logger(self.log)

        _DEFAULT_CONF = self.httpclient
