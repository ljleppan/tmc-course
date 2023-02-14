import logging
from unittest.mock import ANY, call, patch

import pytest
import responses

from testing.util import assert_dir_equals, normalized_filecmp
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


def test_is_valid_course(test_resource_dir):
    assert tmc_course.is_valid_course(test_resource_dir / "valid_course")


def test_is_valid_course_nonexistant(tmp_path):
    assert not tmc_course.is_valid_course(tmp_path / "no_such")


def test_is_valid_course_not_dir(tmp_path):
    filepath = tmp_path / "file.txt"
    filepath.touch()
    assert not tmc_course.is_valid_course(filepath)


def test_is_valid_course_no_tmcproject_yml(tmp_path):
    dirpath = tmp_path / "dir"
    dirpath.mkdir()
    assert not tmc_course.is_valid_course(dirpath)


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


def test_is_valid_part(test_resource_dir):
    assert tmc_course.is_valid_part(test_resource_dir / "valid_course" / "valid_part")


def test_is_valid_part_checks_exists(tmp_course):
    assert not tmc_course.is_valid_part(tmp_course / "no-such")


def test_is_valid_part_checks_is_dir(tmp_course):
    (tmp_course / "file.txt").touch()
    assert not tmc_course.is_valid_part(tmp_course / "file.txt")


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
    assert normalized_filecmp(zip_resource, tmp_path / "tmc-python-tester.zip")


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
    assert normalized_filecmp(zip_resource, tmp_path / "tmc-python-tester.zip")


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
def test_init_assignment_en(test_resource_dir, tmp_part):
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


@responses.activate
def test_init_assignment_fi(test_resource_dir, tmp_part):
    url = (
        "https://github.com/testmycode/tmc-python-tester/archive/refs/heads/master.zip"
    )
    zip_resource = test_resource_dir / "tmc-python-tester.zip"
    with zip_resource.open("rb") as zip_handle:
        responses.get(url=url, body=zip_handle.read())
        tmc_course.init_assignment(
            tmp_part.parent, tmp_part.name, "valid_assignment_fi", "fi"
        )

    assert_dir_equals(
        test_resource_dir / "valid_course" / "valid_part" / "valid_assignment_fi",
        tmp_part / "valid_assignment_fi",
        ignore=["__pycache__"],
    )


@pytest.mark.parametrize("name", (".foo", "foo bar", "foo/bar", "foo-bar"))
def test_init_assignment_invalid_name(tmp_part, name):
    with pytest.raises(ValueError):
        tmc_course.init_assignment(tmp_part.parent, tmp_part.name, name, "en")


def test_init_assignment_tgt_exists_asks_user(tmp_part):
    (tmp_part / "assg1").mkdir()
    with patch.object(tmc_course, "check_from_user") as mock:
        tmc_course.init_assignment(tmp_part.parent, tmp_part.name, "assg1", "en")
        mock.assert_called_once()


def test_is_valid_assignment(test_resource_dir):
    assert tmc_course.is_valid_assignment(
        test_resource_dir / "valid_course" / "valid_part" / "valid_assignment_en"
    )


def test_is_valid_assignment_not_exist(tmp_path):
    assert not tmc_course.is_valid_assignment(tmp_path / "nosuch")


def test_is_valid_assignment_not_dir(tmp_path):
    (tmp_path / "file.txt").touch()
    assert not tmc_course.is_valid_assignment(tmp_path / "file.txt")


def test_is_valid_assignment_no_tmcprojectyml(tmp_path):
    (tmp_path / "assg").mkdir()
    assert not tmc_course.is_valid_assignment(tmp_path / "assg")


@responses.activate
def test_update_course(tmp_course, test_resource_dir):
    url = (
        "https://github.com/testmycode/tmc-python-tester/archive/refs/heads/master.zip"
    )
    zip_resource = test_resource_dir / "tmc-python-tester.zip"
    with zip_resource.open("rb") as zip_handle:
        responses.get(url=url, body=zip_handle.read())

        tmc_course.init_part(tmp_course, "part01")
        tmc_course.init_assignment(tmp_course, "part01", "valid_assignment_fi", "fi")
        tmc_course.init_assignment(tmp_course, "part01", "valid_assignment_en", "en")
        tmc_course.init_assignment(tmp_course, "part01", "assg03", "en")

        tmc_course.init_part(tmp_course, "part02")
        tmc_course.init_assignment(tmp_course, "part02", "valid_assignment_fi", "fi")
        tmc_course.init_assignment(tmp_course, "part02", "valid_assignment_en", "en")

    # add non-assignment dir
    (tmp_course / "part01" / "utils" / "src").mkdir(parents=True)
    (tmp_course / "part01" / "utils" / "src" / "file.txt").touch()

    # modify /tmc/
    (tmp_course / "part01" / "valid_assignment_fi" / "tmc" / "hmac_writer.py").unlink()
    (tmp_course / "part01" / "valid_assignment_en" / "tmc" / "runner.py").unlink()
    (tmp_course / "part01" / "assg03" / "tmc" / "hmac_writer.py").unlink()
    (tmp_course / "part02" / "valid_assignment_fi" / "tmc" / "reflect.py").unlink()
    (tmp_course / "part02" / "valid_assignment_en" / "tmc" / "utils.py").unlink()

    (tmp_course / "part01" / "valid_assignment_en" / "tmc" / "points.py").open(
        "w"
    ).write("MODIFIED")
    (tmp_course / "part02" / "valid_assignment_fi" / "tmc" / "points.py").open(
        "w"
    ).write("MODIFIED")

    # modify /src/ and /test/
    (tmp_course / "part01" / "assg03" / "src" / "solution.py").open("w").write(
        "DO NOT OVERWRITE"
    )
    (tmp_course / "part01" / "assg03" / "test" / "test_solution.py").open("w").write(
        "TEST DATA"
    )

    with zip_resource.open("rb") as zip_handle:
        responses.get(url=url, body=zip_handle.read())
        tmc_course.update_course(tmp_course)

    # Updates all in a part
    assert_dir_equals(
        test_resource_dir
        / "valid_course"
        / "valid_part"
        / "valid_assignment_fi"
        / "tmc",
        tmp_course / "part01" / "valid_assignment_fi" / "tmc",
        ignore=["__pycache__"],
    )
    assert_dir_equals(
        test_resource_dir
        / "valid_course"
        / "valid_part"
        / "valid_assignment_en"
        / "tmc",
        tmp_course / "part01" / "valid_assignment_en" / "tmc",
        ignore=["__pycache__"],
    )
    assert_dir_equals(
        test_resource_dir
        / "valid_course"
        / "valid_part"
        / "valid_assignment_en"
        / "tmc",
        tmp_course / "part01" / "assg03" / "tmc",
        ignore=["__pycache__"],
    )

    # Updates all parts
    assert_dir_equals(
        test_resource_dir
        / "valid_course"
        / "valid_part"
        / "valid_assignment_en"
        / "tmc",
        tmp_course / "part02" / "valid_assignment_en" / "tmc",
        ignore=["__pycache__"],
    )

    # Doesn't touch /src/ or /test/
    assert (
        tmp_course / "part01" / "assg03" / "src" / "solution.py"
    ).read_text() == "DO NOT OVERWRITE"
    assert (
        tmp_course / "part01" / "assg03" / "test" / "test_solution.py"
    ).read_text() == "TEST DATA"

    # Didn't touch the util dir
    assert len(list((tmp_course / "part01" / "utils" / "src").iterdir())) == 1
    assert len(list((tmp_course / "part01" / "utils").iterdir())) == 1


def test_main_init_course(tmp_path):
    course_paths = [tmp_path / "NewCourse1", tmp_path / "NewCourse2"]
    with patch.object(tmc_course, "init_course") as mock:
        tmc_course.main(["init", "course", str(course_paths[0]), str(course_paths[1])])
        mock.assert_has_calls(
            [
                call(course_paths[0]),
                call(course_paths[1]),
            ],
            any_order=True,
        )


def test_main_init_part(tmp_course):
    part_paths = [tmp_course / "part01", tmp_course / "part02"]
    with patch.object(tmc_course, "init_part") as mock:
        tmc_course.main(["init", "part", str(part_paths[0]), str(part_paths[1])])
        mock.assert_has_calls(
            [
                call(tmp_course, "part01"),
                call(tmp_course, "part02"),
            ],
            any_order=True,
        )


def test_main_init_assignment(tmp_course):
    assg_paths = [tmp_course / "part01" / "assg1", tmp_course / "part01" / "assg2"]
    with patch.object(tmc_course, "init_assignment") as mock:
        tmc_course.main(
            ["init", "assignment", str(assg_paths[0]), str(assg_paths[1]), "-f"]
        )
        mock.assert_has_calls(
            [
                call(tmp_course, "part01", "assg1", "fi"),
                call(tmp_course, "part01", "assg2", "fi"),
            ],
            any_order=True,
        )


def test_main_init_assignment_en(tmp_course):
    assg_paths = [tmp_course / "part01" / "assg1", tmp_course / "part01" / "assg2"]
    with patch.object(tmc_course, "init_assignment") as mock:
        tmc_course.main(
            ["init", "assignment", str(assg_paths[0]), str(assg_paths[1]), "-e"]
        )
        mock.assert_has_calls(
            [
                call(tmp_course, "part01", "assg1", "en"),
                call(tmp_course, "part01", "assg2", "en"),
            ],
            any_order=True,
        )


def test_main_update(tmp_course):
    with patch.object(tmc_course, "update_course") as mock:
        tmc_course.main(["update", str(tmp_course)])
        mock.assert_called_once_with(tmp_course)


def test_verbosity_quiet():
    with patch.object(tmc_course, "update_course"):
        with patch.object(tmc_course.logging, "basicConfig") as mock_logging:
            tmc_course.main(["--quiet", "update", "nosuchcourse"])
            mock_logging.assert_called_once_with(format=ANY, level=logging.WARNING)


def test_verbosity_normal():
    with patch.object(tmc_course, "update_course"):
        with patch.object(tmc_course.logging, "basicConfig") as mock_logging:
            tmc_course.main(["update", "nosuchcourse"])
            mock_logging.assert_called_once_with(format=ANY, level=logging.INFO)


def test_verbosity_verbose():
    with patch.object(tmc_course, "update_course"):
        with patch.object(tmc_course.logging, "basicConfig") as mock_logging:
            tmc_course.main(["--verbose", "update", "nosuchcourse"])
            mock_logging.assert_called_once_with(format=ANY, level=logging.DEBUG)
