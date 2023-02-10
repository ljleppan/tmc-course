import argparse
import importlib.resources
import logging
import shutil
import subprocess
import zipfile
from enum import Enum, auto
from pathlib import Path
from typing import Literal

import requests

TMC_PYTHON_TESTER_ZIP_URL = (
    "https://github.com/testmycode/tmc-python-tester/archive/refs/heads/master.zip"
)


class ActionCancelledException(BaseException):
    pass


class SkeletonFile(Enum):
    COURSE_GITIGNORE = auto()
    COURSE_TMCPROJECT_YML = auto()
    ASSIGNMENT_TMCPROJECT_YML = auto()
    ASSIGNMENT_SOLUTION_EN = auto()
    ASSIGNMENT_SOLUTION_FI = auto()
    ASSIGNMENT_TEST_EN = auto()
    ASSIGNMENT_TEST_FI = auto()


def check_from_user(
    message: str, quit_default: bool = True, continue_on_y: bool = True
) -> None:
    quit_char = "n" if continue_on_y else "y"
    continue_char = "y" if continue_on_y else "n"
    suffix = "["
    suffix += continue_char if quit_default else continue_char.upper()
    suffix += quit_char.upper() if quit_default else quit_char
    suffix += "]"

    print(message + " " + suffix)

    response = input("> ").casefold()
    if response == quit_char:
        raise ActionCancelledException
    elif response != continue_char and quit_default:
        raise ActionCancelledException


def add_skeleton_file(skeleton_file: SkeletonFile, path: Path) -> None:
    logging.debug(f"Copying resource {skeleton_file.name} to {path}")
    template_file_name = skeleton_file.name.casefold() + ".template"
    resource_path = importlib.resources.files("tmc_course.resources").joinpath(
        template_file_name
    )
    logging.debug(f"Template file path is {resource_path}")
    shutil.copy(Path(str(resource_path)), path)


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
    if not course_path.is_dir():
        raise ValueError("Course root is not a directory")
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
    if not (course_path / part_name).is_dir():
        raise ValueError(f"{course_path / part_name} is not a directory")
    logging.debug(f"{course_path / part_name} is a valid course part")


def create_src_skeleton(assignment_path: Path, language: Literal["en", "fi"]) -> None:
    if language not in ("fi", "en"):
        raise ValueError("Language must be 'fi' or 'en'")

    logging.debug(f'Creating " {assignment_path / "src"}')
    (assignment_path / "src").mkdir(exist_ok=True)

    logging.debug('Creating {assignment_path / "src" / "__init__.py"}"')
    (assignment_path / "src" / "__init__.py").touch(exist_ok=True)

    if language == "en":
        add_skeleton_file(
            SkeletonFile.ASSIGNMENT_SOLUTION_EN,
            assignment_path / "src" / "solution.py",
        )
    else:
        add_skeleton_file(
            SkeletonFile.ASSIGNMENT_SOLUTION_FI,
            assignment_path / "src" / "ratkaisu.py",
        )


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
    file_contents = file_contents.replace("POINTNAME", assignment_name)
    with test_file_path.open("w") as fh:
        fh.write(file_contents)
    logging.debug("Test skeleton complete")


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


def assert_valid_assignment(assignment_path: Path) -> None:
    if not assignment_path.exists():
        raise ValueError(f"Assignment {assignment_path} does not exist")
    if not assignment_path.is_dir():
        raise ValueError("Assignment {assignment_path} is not a directory")
    logging.debug(f"{assignment_path} is a valid course part")
    if not any(
        filepath.name == ".tmcproject.yml" for filepath in assignment_path.iterdir()
    ):
        raise ValueError(
            "{assignment_path} is not a TMC assignment (missing .tmcproject.yml)"
        )
    logging.debug(f"{assignment_path} is a valid TMC course")


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
    logging.info(f"Running tests for course {course_path}")
    assert_valid_course(course_path)

    assignments: list[Path] = []
    for maybe_part in course_path.iterdir():
        try:
            assert_valid_part(course_path, maybe_part.name)
        except ValueError:
            continue
        for maybe_assignment in maybe_part.iterdir():
            try:
                assert_valid_assignment(maybe_assignment)
            except ValueError:
                continue
            assignments.append(maybe_assignment)
    run_tests(assignments)


def test_part(course_path: Path, part_name: str) -> None:
    assert_valid_course(course_path)
    assert_valid_part(course_path, part_name)
    part_path = course_path / part_name

    assignments: list[Path] = []
    for maybe_assignment in part_path.iterdir():
        try:
            assert_valid_assignment(maybe_assignment)
        except ValueError:
            pass
        assignments.append(maybe_assignment)
    run_tests(assignments)


def test_assignment(course_path: Path, part_name: str, assignment_name: str) -> None:
    assert_valid_course(course_path)
    assert_valid_part(course_path, part_name)
    assert_valid_assignment(course_path / part_name / assignment_name)

    run_tests([course_path / part_name / assignment_name])


def run_tests(assignment_paths: list[Path]) -> None:
    results: dict[Path, tuple[int, str, str]] = {}
    for assignment in assignment_paths:
        results[assignment] = run_test(assignment)
    if all(r[0] == 0 for r in results.values()):
        logging.info("All tests passed")
    else:
        logging.warning("Following tests failed:")
        for assignment, (status, stdout, stderr) in results.items():
            if status != 0:
                logging.warning(f"{assignment}: status code {status}")
                logging.info(f"STDOUT:\n{stdout}")
                logging.info(f"STDERR:\n{stderr}")
                logging.info("--------")


def run_test(assignment_path: Path) -> tuple[int, str, str]:
    result = subprocess.run(["python3", "-m", "tmc"], cwd=assignment_path)
    logging.info(
        f"{assignment_path}: {'SUCCESS' if result.returncode == 0 else 'FAIL'}"
    )
    return result.returncode, str(result.stdout), str(result.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        "tmc-course",
        description="Helper for building TestMyCode python programming courses",
    )

    verbosity_grp = parser.add_mutually_exclusive_group()
    verbosity_grp.add_argument(
        "--quiet", action="store_true", help="Only output warning"
    )
    verbosity_grp.add_argument(
        "--verbose", action="store_true", help="Output debugging information"
    )

    actions = parser.add_subparsers(
        dest="action",
        required=True,
        metavar="ACTION",
    )

    # INIT
    init_grp = actions.add_parser(
        "init", help="Initialize a new course, part or assignment"
    )
    init_actions = init_grp.add_subparsers(
        dest="init_action", required=True, metavar="TYPE"
    )

    # INIT COURSE
    init_course_grp = init_actions.add_parser("course", help="Initialize a new course")
    init_course_grp.add_argument(
        "course_path", type=str, help="Course root directory (should not exist)"
    )

    # INIT PART
    init_part_grp = init_actions.add_parser("part", help="Initialize a new course part")
    init_part_grp.add_argument("course_path", type=str, help="Course root directory")
    init_part_grp.add_argument(
        "part", type=str, nargs="+", help="Name(s) of part(s) to initialize"
    )

    # INIT ASSIGNMENT
    init_assignment_grp = init_actions.add_parser(
        "assignment", help="Initialize a assignment"
    )
    init_assignment_grp.add_argument(
        "course_path", type=str, help="Course root directory"
    )
    init_assignment_grp.add_argument(
        "part", type=str, help="Name of part assignment(s) belong to"
    )
    init_assignment_grp.add_argument(
        "assignment", type=str, nargs="+", help="Name(s) of assignment(s) to initialize"
    )
    language_grp = init_assignment_grp.add_mutually_exclusive_group(required=True)
    language_grp.add_argument(
        "-e", "--english", action="store_true", help="Use English language templates"
    )
    language_grp.add_argument(
        "-f", "--finnish", action="store_true", help="Use Finnish language templates"
    )

    # TEST
    test_grp = actions.add_parser("test", help="Test a new course, part or assignment")
    test_grp.add_argument("course_path", type=str, help="Course root directory")
    test_grp.add_argument("part", type=str, help="Name of part")
    test_grp.add_argument("assignment", type=str, help="Name of assignment")

    # UPDATE
    update_grp = actions.add_parser(
        "update", help="Update TMC-python-runner embedded in assignments"
    )
    update_grp.add_argument("course_path", type=str, help="Course root directory")

    # Verbosity control
    args = parser.parse_args(argv)
    if not (args.quiet or args.verbose):
        logging.basicConfig(format="%(message)s", level=logging.INFO)
    if args.quiet:
        logging.basicConfig(format="%(message)s", level=logging.WARNING)
    if args.verbose:
        logging.basicConfig(
            format="%(levelname)s:%(asctime)s: %(message)s", level=logging.DEBUG
        )

    logging.error(args)

    try:
        if args.action == "init":
            if args.init_action == "course":
                init_course(Path(args.course_path))
            elif args.init_action == "part":
                for part in args.part:
                    init_part(Path(args.course_path), part)
            elif args.init_action == "assignment":
                language: Literal["fi", "en"] = "fi" if args.finnish else "en"
                for assignment in args.assignments:
                    init_assignment(
                        Path(args.course_path), args.part, assignment, language
                    )
        if args.action == "test":
            if args.part and args.assignments:
                test_assignment(args.course_path, args.part, args.assignment)
            elif args.part:
                test_part(args.course_path, args.part)
            else:
                test_course(args.course_path)
        if args.action == "update":
            update_course(args.course_path)
    except ActionCancelledException:
        print("OK, quitting")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
