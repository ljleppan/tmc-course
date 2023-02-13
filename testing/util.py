import filecmp
from pathlib import Path
from typing import Optional


def test_resource_dir() -> Path:
    return Path(__file__).parent / "resources"


def normalized_filecmp(
    expected_file: Path, actual_file: Path, ignore_newlines: bool = True
) -> bool:
    """Compares two files ignoring the type of the newline, because TMC does it's
    own magic down the line anyways.

    It should be enough to open() both files, as python apparently just converts
    to universal-mode newlines at that point. For binary files, we can fall back
    to filecmp.cmp.
    """
    with expected_file.open("r") as expected_fh, actual_file.open("r") as actual_fh:
        try:
            expected_lines = expected_fh.readlines()
            actual_lines = actual_fh.readlines()
        except UnicodeDecodeError:
            # Binary files, just filecmp.cmp because there are no newlines at this point
            return filecmp.cmp(expected_file, actual_file)
    if len(expected_lines) != len(actual_lines):
        return False
    for expected_line, actual_line in zip(expected_lines, actual_lines):
        if expected_line != actual_line:
            return False
    return True


def assert_dir_equals(
    expected_path: Path, actual_path: Path, ignore: Optional[list[str]] = None
) -> None:
    # filecmp.dircmp is silly and only checks the os.stat() signature, which means it
    # ignores contents but enforces modification time. This means both a risk of
    # false positives and false negatives, which is impressive on it's own.
    expected_files = list(expected_path.iterdir())
    actual_files = list(actual_path.iterdir())

    if ignore:
        expected_files = [f for f in expected_files if f.name not in ignore]
        actual_files = [f for f in actual_files if f.name not in ignore]

    expected_filenames = set(f.name for f in expected_files)
    actual_filenames = set(f.name for f in actual_files)
    assert expected_filenames == actual_filenames, (
        "File name sets are not equivalent; ",
        f"{expected_filenames=}, {actual_filenames=}; ",
        f"diff: {expected_filenames.symmetric_difference(actual_filenames)}",
    )

    # Doing what filecmp.dircmp *should* be doing
    expected_files = sorted(expected_files)
    actual_files = sorted(actual_files)
    for expected_file, actual_file in zip(expected_files, actual_files):
        assert (
            expected_file.name == actual_file.name
        ), f"File names differ; {expected_file.name=}, {actual_file.name=}"
        if expected_file.is_dir():
            assert_dir_equals(expected_file, actual_file)
        else:
            assert normalized_filecmp(
                expected_file, actual_file
            ), f"File contents differ; {expected_file=}, {actual_file=}"
