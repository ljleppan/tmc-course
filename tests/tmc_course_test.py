import filecmp
from unittest.mock import patch

import pytest
import responses

from testing.util import assert_dir_equals
from tmc_course import tmc_course


@pytest.mark.parametrize(
    "user_input, quit_default, continue_on_y",
    (
        ("", True, False),
        ("", True, True),
        ("y", True, False),
        ("y", False, False),
        ("n", True, True),
        ("n", False, True),
        ("Y", True, False),
        ("Y", False, False),
    ),
)
def test_check_from_user_quits(user_input, quit_default, continue_on_y, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: user_input)
    with pytest.raises(tmc_course.ActionCancelledException):
        tmc_course.check_from_user("msg", quit_default, continue_on_y)


@pytest.mark.parametrize(
    "user_input, quit_default, continue_on_y",
    (
        ("", False, False),
        ("", False, True),
        ("y", True, True),
        ("y", False, True),
        ("n", True, False),
        ("n", False, False),
        ("Y", True, True),
        ("Y", False, True),
        ("N", True, False),
        ("N", False, False),
    ),
)
def test_check_from_user_continues(
    user_input, quit_default, continue_on_y, monkeypatch
):
    monkeypatch.setattr("builtins.input", lambda _: user_input)
    tmc_course.check_from_user("msg", quit_default, continue_on_y)


@pytest.mark.parametrize("resource_name", list(tmc_course.SkeletonFile))
def test_all_resources_exist(resource_name, tmp_path):
    tmp_file = tmp_path / "output.tmp"
    tmc_course.add_skeleton_file(resource_name, tmp_file)
    assert len(tmp_file.read_text()) > 1


def test_add_skeleton_file(tmp_path):
    tmp_file = tmp_path / "output.tmp"
    tmc_course.add_skeleton_file(
        tmc_course.SkeletonFile.COURSE_TMCPROJECT_YML, tmp_file
    )
    assert (
        tmp_file.read_text()
        == 'sandbox_image: "eu.gcr.io/moocfi-public/tmc-sandbox-python"\n'
    )


def test_init_course(tmp_path):
    course_path = tmp_path / "NewCourse"
    tmc_course.init_course(course_path)
    assert (course_path / ".gitignore").exists()
    assert (course_path / ".tmcproject.yml").exists()


def test_init_course_existing_checks_user(tmp_path, monkeypatch):
    course_path = tmp_path / "NewCourse"
    course_path.mkdir()
    with patch.object(tmc_course, "check_from_user") as mock:
        tmc_course.init_course(course_path)
        mock.assert_called_once()


@pytest.mark.parametrize("name", ("-foo-" "foo bar", "baz-bar", ".foo"))
def test_init_course_invalid_name(tmp_path, name):
    course_dir = tmp_path / name
    with pytest.raises(ValueError):
        tmc_course.init_course(course_dir)


@pytest.mark.parametrize("name", ("bar", "foo_bar", "foo1", "1_foo"))
def test_init_course_valid_name(tmp_path, name):
    tmc_course.init_course(tmp_path / name)


def test_assert_valid_course(test_resource_dir):
    tmc_course.assert_valid_course(test_resource_dir / "valid_course")


def test_assert_valid_course_nonexistant(tmp_path):
    with pytest.raises(ValueError):
        tmc_course.assert_valid_course(tmp_path / "no_such")


def test_assert_valid_course_not_dir(tmp_path):
    filepath = tmp_path / "file.txt"
    filepath.touch()
    with pytest.raises(ValueError):
        tmc_course.assert_valid_course(filepath)


def test_assert_valid_course_no_tmcproject_yml(tmp_path):
    dirpath = tmp_path / "dir"
    dirpath.mkdir()
    with pytest.raises(ValueError):
        tmc_course.assert_valid_course(dirpath)


def test_init_part(tmp_course):
    tmc_course.init_part(tmp_course, "part01")


def test_init_part_validates_course(tmp_path):
    course_path = tmp_path / "NewCourse"
    course_path.mkdir()
    with pytest.raises(ValueError):
        tmc_course.init_part(course_path, "part01")


@pytest.mark.parametrize("name", ("foo-bar", ".foo", "foo/bar"))
def test_init_part_checks_name(tmp_course, name):
    with pytest.raises(ValueError):
        tmc_course.init_part(tmp_course, name)


def test_init_part_checks_if_exists(tmp_course):
    (tmp_course / "part01").mkdir()
    with patch.object(tmc_course, "check_from_user") as mock:
        tmc_course.init_part(tmp_course, "part01")
        mock.assert_called_once()


def test_assert_valid_part(test_resource_dir):
    tmc_course.assert_valid_part(test_resource_dir / "valid_course", "valid_part")


def test_assert_valid_part_checks_exists(tmp_course):
    with pytest.raises(ValueError):
        tmc_course.assert_valid_part(tmp_course, "no-such")


def test_assert_valid_part_checks_is_dir(tmp_course):
    (tmp_course / "file.txt").touch()
    with pytest.raises(ValueError):
        tmc_course.assert_valid_part(tmp_course, "file.txt")


def test_create_src_skeleton_fi(tmp_path, test_resource_dir):
    tmc_course.create_src_skeleton(tmp_path, "fi")

    solution_file = tmp_path / "src" / "ratkaisu.py"
    expected = (
        test_resource_dir
        / "valid_course"
        / "valid_part"
        / "valid_assignment_fi"
        / "src"
        / "ratkaisu.py"
    )
    assert solution_file.exists()
    assert solution_file.read_text() == expected.read_text()

    init_py = tmp_path / "src" / "__init__.py"
    assert init_py.exists()
    assert init_py.read_text() == ""


def test_create_src_skeleton_en(tmp_path, test_resource_dir):
    tmc_course.create_src_skeleton(tmp_path, "en")

    solution_file = tmp_path / "src" / "solution.py"
    expected = (
        test_resource_dir
        / "valid_course"
        / "valid_part"
        / "valid_assignment_en"
        / "src"
        / "solution.py"
    )
    assert solution_file.exists()
    assert solution_file.read_text() == expected.read_text()

    init_py = tmp_path / "src" / "__init__.py"
    assert init_py.exists()
    assert init_py.read_text() == ""


def test_create_src_skeleton_invalid_language(tmp_path):
    with pytest.raises(ValueError):
        tmc_course.create_src_skeleton(tmp_path, "nosuchlanguage")


def test_create_test_skeleton_fi(tmp_path, test_resource_dir):
    tmc_course.create_test_skeleton(tmp_path, "valid_assignment_fi", "fi")

    test_file = tmp_path / "test" / "test_ratkaisu.py"
    expected = (
        test_resource_dir
        / "valid_course"
        / "valid_part"
        / "valid_assignment_fi"
        / "test"
        / "test_ratkaisu.py"
    )
    assert test_file.exists()
    assert test_file.read_text() == expected.read_text()

    init_py = tmp_path / "test" / "__init__.py"
    assert init_py.exists()
    assert init_py.read_text() == ""


def test_create_test_skeleton_en(tmp_path, test_resource_dir):
    tmc_course.create_test_skeleton(tmp_path, "valid_assignment_en", "en")

    test_file = tmp_path / "test" / "test_solution.py"
    expected = (
        test_resource_dir
        / "valid_course"
        / "valid_part"
        / "valid_assignment_en"
        / "test"
        / "test_solution.py"
    )
    assert test_file.exists()
    assert test_file.read_text() == expected.read_text()

    init_py = tmp_path / "test" / "__init__.py"
    assert init_py.exists()
    assert init_py.read_text() == ""


def test_create_test_skeleton_invalid_language(tmp_path):
    with pytest.raises(ValueError):
        tmc_course.create_test_skeleton(tmp_path, "solution", "nosuchlanguage")


@responses.activate
def test_download_tmc_python_tester(test_resource_dir, tmp_path):
    url = (
        "https://github.com/testmycode/tmc-python-tester/archive/refs/heads/master.zip"
    )
    zip_resource = test_resource_dir / "tmc-python-tester.zip"
    with zip_resource.open("rb") as zip_handle:
        responses.get(url=url, body=zip_handle.read())
        tmc_course.download_tmc_python_tester(tmp_path, update=True)
    responses.assert_call_count(url, 1)
    assert filecmp.cmp(zip_resource, tmp_path / "tmc-python-tester.zip", shallow=False)


def test_download_tmc_python_tester_skips_no_update(tmp_path):
    with patch.object(tmc_course, "requests") as mock:
        (tmp_path / "tmc-python-tester.zip").touch()
        tmc_course.download_tmc_python_tester(tmp_path, update=False)
        mock.assert_not_called()


@responses.activate
def test_download_tmc_python_tester_updates(test_resource_dir, tmp_path):
    (tmp_path / "tmc-python-tester.zip").touch()

    url = (
        "https://github.com/testmycode/tmc-python-tester/archive/refs/heads/master.zip"
    )
    zip_resource = test_resource_dir / "tmc-python-tester.zip"
    with zip_resource.open("rb") as zip_handle:
        responses.get(url=url, body=zip_handle.read())
        tmc_course.download_tmc_python_tester(tmp_path, update=True)

    responses.assert_call_count(url, 1)
    assert filecmp.cmp(zip_resource, tmp_path / "tmc-python-tester.zip", shallow=False)


@responses.activate
def test_create_tmc_dir(test_resource_dir, tmp_part):
    expected_path = (
        test_resource_dir
        / "valid_course"
        / "valid_part"
        / "valid_assignment_en"
        / "tmc"
    )
    assg_path = tmp_part / "assg01"
    assg_path.mkdir()

    url = (
        "https://github.com/testmycode/tmc-python-tester/archive/refs/heads/master.zip"
    )
    zip_resource = test_resource_dir / "tmc-python-tester.zip"
    with zip_resource.open("rb") as zip_handle:
        responses.get(url=url, body=zip_handle.read())
        tmc_course.create_tmc_dir(assg_path)

    assert_dir_equals(expected_path, assg_path / "tmc")


@responses.activate
def test_init_assignment(test_resource_dir, tmp_part):
    url = (
        "https://github.com/testmycode/tmc-python-tester/archive/refs/heads/master.zip"
    )
    zip_resource = test_resource_dir / "tmc-python-tester.zip"
    with zip_resource.open("rb") as zip_handle:
        responses.get(url=url, body=zip_handle.read())
        tmc_course.init_assignment(
            tmp_part.parent, tmp_part.name, "valid_assignment_en", "en"
        )

    assert_dir_equals(
        test_resource_dir / "valid_course" / "valid_part" / "valid_assignment_en",
        tmp_part / "valid_assignment_en",
        ignore=["__pycache__"],
    )
