from pydantic_settings import BaseSettings, SettingsConfigDict

from pypaladin import log
from pypaladin import httpclient
from pypaladin.log import LogConfig
from pypaladin_orm import objects


class BaseAppConfig(BaseSettings):
    """Base App Configuration"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )

    http_client: httpclient.HTTPClientConfig = httpclient.HTTPClientConfig()
    log: LogConfig = LogConfig()
    db: objects.DBConfig = objects.DBConfig()

    def __init__(self):
        super().__init__()

    def setup(self):
        log.setup_logger(self.log)

        httpclient._DEFAULT_CONF = self.http_client
        objects._DEFAULT_CONF = self.db
