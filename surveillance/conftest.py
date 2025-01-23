import warnings
import pytest


@pytest.fixture(autouse=True)
def ignore_resource_warnings():
    # TODO: actually get rid of the src of warnings
    # TODO: Claude told me to do this
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)


# Fixture allegedly solves
# >       response = await async_client.get("http://127.0.0.1:8000/dashboard/timeline")
# E       AttributeError: 'async_generator' object has no attribute 'get'

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    config.option.asyncio_default_fixture_loop_scope = "function"
