import filecmp
from pathlib import Path


def test_resource_dir() -> Path:
    return Path(__file__).parent / "resources"


def assert_dir_equals(
    expected_path: Path, actual_path: Path, ignore: list[str] | None = None
) -> None:
    # filecmp.dircmp is silly and only checks the os.stat() signature, which means it
    # ignores contents but enforces modification time. This means both a risk of
    # false positives and false negatives, which is impressive on it's own.
    expected_files = list(expected_path.iterdir())
    actual_files = list(actual_path.iterdir())

    if ignore:
        expected_files = [f for f in expected_files if f.name not in ignore]
        actual_files = [f for f in actual_files if f.name not in ignore]

    assert set(f.name for f in expected_files) == set(
        f.name for f in actual_files
    ), f"{expected_files=}, {actual_files=}"

    # Doing what filecmp.dircmp *should* be doing
    expected_files = sorted(expected_files)
    actual_files = sorted(actual_files)
    for expected_file, actual_file in zip(expected_files, actual_files):
        assert (
            expected_file.name == actual_file.name
        ), f"{expected_file.name=}, {actual_file.name=}"
        if expected_file.is_dir():
            assert_dir_equals(expected_file, actual_file)
        else:
            assert filecmp.cmp(
                expected_file, actual_file, shallow=False
            ), f"{expected_file=}, {actual_file=}"
