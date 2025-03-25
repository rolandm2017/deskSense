import warnings
import pytest

import sys
from pathlib import Path


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



#
# # Make the tests run fine on both Ubuntu AND Windows
#

# Get the absolute path to the project root
project_root = Path(__file__).absolute().parent

# Add both the project root and the src directory to the path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Print paths for debugging
print(f"Project root added to path: {project_root}")
print(f"Sys path: {sys.path}")