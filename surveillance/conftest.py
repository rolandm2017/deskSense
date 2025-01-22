import warnings
import pytest


@pytest.fixture(autouse=True)
def ignore_resource_warnings():
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)


pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    config.option.asyncio_default_fixture_loop_scope = "function"
