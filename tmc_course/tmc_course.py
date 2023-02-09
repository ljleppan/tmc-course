import logging
import shutil
import zipfile
from enum import Enum, auto
from pathlib import Path
from typing import Literal

import requests

RESOURCE_PATH = Path(__file__).parent / "resources"
TMC_PYTHON_TESTER_ZIP_URL = (
    "https://github.com/testmycode/tmc-python-tester/archive/refs/heads/master.zip"
)


class UserExitException(BaseException):
    pass


class SkeletonFile(Enum):
    COURSE_GITIGNORE = auto()
    COURSE_TMCPROJECT_YML = auto()
    ASSIGNMENT_TMCPROJECT_YML = auto()
    ASSIGNMENT_SOLUTION_EN = auto()
    ASSIGNMENT_SOLUTION_FI = auto()
    ASSIGNMENT_TEST_EN = auto()
    ASSIGNMENT_TEST_FI = auto()


def check_from_user(message: str, quit_on_y: bool = False) -> None:
    suffix = "[Yn]" if quit_on_y else "[yN]"
    print(message + " " + suffix)
    response = input("> ")
    if response.casefold() == "y" and quit_on_y:
        raise UserExitException
    elif response.casefold() == "n" or quit_on_y:
        raise UserExitException


def add_skeleton_file(skeleton_file: SkeletonFile, path: Path) -> None:
    logging.debug(f"Copying resource {skeleton_file.name} to {path}")
    template_file_name = skeleton_file.name.casefold() + ".template"
    shutil.copy(RESOURCE_PATH / template_file_name, path)


def init_course(course_path: Path) -> None:
    logging.info(f"Initializing a new course in {course_path}")
    if course_path.exists():
        check_from_user(
            f"Directory {course_path} already exists. Continue and overwrite?"
        )

    if not course_path.name.replace("_", "").isalnum():
        raise ValueError("Course name must be alphanumeric (underscores allowed)")

    logging.debug(f"Creating directory {course_path}")
    course_path.mkdir(exist_ok=True, parents=True)

    add_skeleton_file(SkeletonFile.COURSE_GITIGNORE, course_path / ".gitignore")
    add_skeleton_file(
        SkeletonFile.COURSE_TMCPROJECT_YML, course_path / ".tmcproject.yml"
    )


def assert_valid_course(course_path: Path) -> None:
    if not course_path.exists():
        raise ValueError("Course root directory does not exist")
    if not any(
        filepath.name == ".tmcproject.yml" for filepath in course_path.iterdir()
    ):
        raise ValueError(
            "Course root does not appear to be a TMC course (missing .tmcproject.yml)"
        )
    logging.debug(f"{course_path} is a valid TMC course")


def init_part(course_path: Path, part_name: str) -> None:
    assert_valid_course(course_path)

    if not part_name.replace("_", "").isalnum():
        raise ValueError("Part name must be alphanumeric (underscores allowed)")

    part_path = course_path / part_name
    logging.info(f"Initializing a new part in {part_path}")

    if part_path.exists():
        check_from_user(
            f"Directory {part_path} already exists. Continue and overwrite?"
        )
    logging.debug(f"Creating directory {part_path}")
    part_path.mkdir(exist_ok=True)


def assert_valid_part(course_path: Path, part_name: str) -> None:
    if not (course_path / part_name).exists():
        raise ValueError(f"Part {part_name} does not exist")
    logging.debug(f"{course_path / part_name} is a valid course part")


def create_src_skeleton(assignment_path: Path, language: Literal["en", "fi"]) -> None:
    logging.debug(f'Creating " {assignment_path / "src"}')
    (assignment_path / "src").mkdir(exist_ok=True)

    logging.debug('Creating {assignment_path / "src" / "__init__.py"}"')
    (assignment_path / "src" / "__init__.py").touch(exist_ok=True)

    if language == "en":
        add_skeleton_file(
            SkeletonFile.ASSIGNMENT_SOLUTION_EN,
            assignment_path / "src" / "solution.py",
        )
    elif language == "fi":
        add_skeleton_file(
            SkeletonFile.ASSIGNMENT_SOLUTION_FI,
            assignment_path / "src" / "ratkaisu.py",
        )
    else:
        raise ValueError("Language must be 'fi' or 'en'")


def create_test_skeleton(
    assignment_path: Path, assignment_name: str, language: Literal["en", "fi"]
) -> None:
    logging.debug(f'Creating {assignment_path / "test"}')
    (assignment_path / "test").mkdir(exist_ok=True)

    logging.debug(f'Creating {assignment_path / "test" / "__init__.py"}')
    (assignment_path / "test" / "__init__.py").touch(exist_ok=True)

    if language == "en":
        test_file_path = assignment_path / "test" / "test_solution.py"
        add_skeleton_file(SkeletonFile.ASSIGNMENT_TEST_EN, test_file_path)
    elif language == "fi":
        test_file_path = assignment_path / "test" / "test_ratkaisu.py"
        add_skeleton_file(SkeletonFile.ASSIGNMENT_TEST_FI, test_file_path)
    else:
        raise ValueError("Language must be 'fi' or 'en'")

    logging.debug("Inserting assignment name into test file")
    with test_file_path.open("r") as fh:
        file_contents = fh.read()
    file_contents.replace("ASSIGNMENTMODULE", assignment_name)
    file_contents.replace("POINTNAME", assignment_name)
    file_contents.replace("TESTNAME", f"{assignment_name.capitalize}Test")
    with test_file_path.open("w") as fh:
        fh.write(file_contents)


def download_tmc_python_tester(course_path: Path, update: bool) -> None:
    tester_zip_path = course_path / "tmc-python-tester.zip"
    logging.debug(
        f'Looking for TMC-python-tester zip at {course_path / "tmc-python-tester.zip"}'
    )

    if update or not tester_zip_path.exists():
        logging.info("Downloading TMC-python-tester")
        logging.debug(f"URL: {TMC_PYTHON_TESTER_ZIP_URL}")
        response = requests.get(TMC_PYTHON_TESTER_ZIP_URL, stream=True)
        with open(tester_zip_path, "wb") as fh:
            for chunk in response.iter_content(chunk_size=128):
                fh.write(chunk)


def create_tmc_dir(assignment_path: Path) -> None:
    logging.debug(f'Creating {assignment_path / "tmc"}')
    (assignment_path / "tmc").mkdir(exist_ok=True)

    course_path = assignment_path.parent.parent
    download_tmc_python_tester(course_path, update=False)

    with zipfile.ZipFile(course_path / "tmc-python-tester.zip") as tester_zip:
        for file_info in tester_zip.infolist():
            if file_info.filename.startswith("tmc-python-tester-master/tmc/"):
                # Need to remove prefix, s.t. we don't retain the parent folders
                file_info.filename.replace("tmc-python-tester-master/tmc/", "")
                logging.debug(
                    f'Extracting {file_info.filename} to {assignment_path / "tmc"}'
                )
                tester_zip.extract(file_info, assignment_path / "tmc")


def init_assignment(
    course_path: Path,
    part_name: str,
    assignment_name: str,
    language: Literal["fi", "en"],
) -> None:
    assert_valid_course(course_path)
    assert_valid_part(course_path, part_name)

    if not assignment_name.replace("_", "").isalnum():
        raise ValueError("Assignment name must be alphanumeric (underscores allowed)")

    assignment_path = course_path / part_name / assignment_name
    logging.info(f"Initializing a new assignment in {assignment_name}")

    if assignment_path.exists():
        check_from_user(
            f"Directory {assignment_path} already exists. Continue and overwrite?"
        )
    logging.debug(f"Creating {assignment_path}")
    assignment_path.mkdir(exist_ok=True)

    add_skeleton_file(
        SkeletonFile.ASSIGNMENT_TMCPROJECT_YML, assignment_path / ".tmcproject.yml"
    )
    create_src_skeleton(assignment_path, language)
    create_test_skeleton(assignment_path, assignment_name, language)
    create_tmc_dir(assignment_path)


def update_course(course_path: Path) -> None:
    logging.info(f"Updating TMC-python-tester for course {course_path}")
    download_tmc_python_tester(course_path, update=True)
    assert_valid_course(course_path)
    for maybe_part in course_path.iterdir():
        logging.debug("Checking whether {maybe_part} is a course part")
        if not maybe_part.is_dir():
            logging.debug("Not a directory, skipping")
            continue
        for maybe_assignment in maybe_part.iterdir():
            logging.debug(f"Checking whether {maybe_assignment} is an assignment")
            if not maybe_assignment.is_dir():
                logging.debug("Not a directory, skipping")
                continue
            if not any(
                fh.name.endswith(".tmcproject.yml") for fh in maybe_assignment.iterdir()
            ):
                logging.debug("Has no .tmcproject.yml, skipping")
                continue
            logging.info(f"Updating assignment at {maybe_assignment}")
            create_tmc_dir(maybe_assignment)


def test_course(course_path: Path) -> None:
    raise NotImplementedError


def test_part(course_path: Path, part_name: str) -> None:
    raise NotImplementedError


def test_assignment(course_path: Path, part_name: str, assignment_name: str) -> None:
    raise NotImplementedError


if __name__ == "__main__":
    create_tmc_dir(Path(__file__).parent.parent / "example_course")
