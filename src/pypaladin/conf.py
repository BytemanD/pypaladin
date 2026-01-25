from typing import Optional, Sequence
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

    @classmethod
    def setup(cls, values: Optional[dict] = None):
        c = cls.model_validate(values or {})
        log.setup_logger(c.log)
        objects.setup_db(c.db)

        httpclient._DEFAULT_CONF = c.http_client
        return c
