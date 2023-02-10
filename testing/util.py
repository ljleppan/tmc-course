from pathlib import Path


def test_resource_dir() -> Path:
    return Path(__file__).parent / "resources"
