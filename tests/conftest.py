from pathlib import Path

import pytest

import testing.util


@pytest.fixture
def test_resource_dir() -> Path:
    return testing.util.test_resource_dir()
