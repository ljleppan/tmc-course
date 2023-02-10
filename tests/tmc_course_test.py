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
