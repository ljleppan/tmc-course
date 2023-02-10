from unittest.mock import patch

import pytest

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
