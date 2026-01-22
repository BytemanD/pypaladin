import pytest

from pypaladin import conf

CONF = conf.BaseAppConfig()


@pytest.fixture(scope="session", autouse=True)
def setup_config():
    CONF.setup()
