import sys
from unittest import mock

import pytest


@pytest.fixture(scope="function", autouse=False)
def smbus2():
    """Mock smbus module."""
    sys.modules["smbus2"] = mock.MagicMock()
    yield sys.modules["smbus2"]
    del sys.modules["smbus2"]


@pytest.fixture(scope="function", autouse=False)
def scd4x():
    """Import scd4x module."""
    import scd4x

    yield scd4x
    del sys.modules["scd4x"]
