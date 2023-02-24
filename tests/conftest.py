from pathlib import Path

import pytest

import testing.util
from tmc_course import tmc_course


@pytest.fixture
def test_resource_path() -> Path:
    return testing.util.test_resource_dir()


@pytest.fixture
def tmp_course(tmp_path) -> Path:
    course_path = tmp_path / "NewCourse"
    tmc_course.init_course(course_path)
    return course_path


@pytest.fixture
def tmp_part(tmp_course) -> Path:
    tmc_course.init_part(tmp_course, "part01")
    return tmp_course / "part01"
