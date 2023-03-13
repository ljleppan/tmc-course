import argparse
import contextlib
import importlib.metadata
import importlib.resources
import logging
import os
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Generator, Literal, Optional

import requests
import treelib  # type: ignore
from tqdm import tqdm

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
    path = path.resolve()
    logging.debug(f"Copying resource {skeleton_file.name} to {path}")
    template_file_name = skeleton_file.name.casefold() + ".template"
    resource_path = importlib.resources.files("tmc_course.resources").joinpath(
        template_file_name
    )
    logging.debug(f"Template file path is {resource_path}")
    shutil.copy(Path(str(resource_path)), path)


def init_course(course_path: Path) -> None:
    course_path = course_path.resolve()
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


def is_valid_course(course_path: Path) -> bool:
    course_path = course_path.resolve()

    if not course_path.exists():
        logging.debug("Course root directory does not exist")
        return False
    if not course_path.is_dir():
        logging.debug("Course root is not a directory")
        return False
    if not any(
        filepath.name == ".tmcproject.yml" for filepath in course_path.iterdir()
    ):
        logging.debug(
            "Course root does not appear to be a TMC course (missing .tmcproject.yml)"
        )
        return False
    logging.debug(f"{course_path} is a valid TMC course")
    return True


def init_part(course_path: Path, part_name: str) -> None:
    course_path = course_path.resolve()

    if not is_valid_course(course_path):
        raise ValueError(f"{course_path} is not a TMC course")

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


def is_valid_part(part: Path) -> bool:
    part = part.resolve()

    if not part.exists():
        logging.debug("Part {part_name} does not exist")
        return False
    if not part.is_dir():
        logging.debug(f"{part} is not a directory")
        return False
    if not is_valid_course(part.parent):
        logging.debug(f"Parent {part.parent} is not valid course")
        return False
    logging.debug(f"{part} is a valid course part")
    return True


def create_src_skeleton(assignment_path: Path, language: Literal["en", "fi"]) -> None:
    assignment_path = assignment_path.resolve()
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
    assignment_path = assignment_path.resolve()
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
    course_path = course_path.resolve()
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
    assignment_path = assignment_path.resolve()
    logging.debug(f'Creating {assignment_path / "tmc"}')
    (assignment_path / "tmc").mkdir(exist_ok=True)

    course_path = assignment_path.parent.parent
    download_tmc_python_tester(course_path, update=False)

    with zipfile.ZipFile(course_path / "tmc-python-tester.zip") as tester_zip:
        for file_info in tester_zip.infolist():
            logging.debug(f"Looking at file {file_info.filename=}")
            if file_info.filename.startswith("tmc-python-tester-master/tmc/"):
                # Need to remove prefix, s.t. we don't retain the parent folders
                file_info.filename = file_info.filename.replace(
                    "tmc-python-tester-master/tmc", ""
                )
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
    course_path = course_path.resolve()
    if not is_valid_course(course_path):
        raise ValueError(f"{course_path} is not a valid TMC course")
    if not is_valid_part(course_path / part_name):
        raise ValueError(f"{course_path / part_name} is not a valid course part")

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


def is_valid_assignment(assignment_path: Path) -> bool:
    assignment_path = assignment_path.resolve()
    if not assignment_path.exists():
        logging.debug(f"Assignment {assignment_path} does not exist")
        return False
    if not assignment_path.is_dir():
        logging.debug(f"Assignment {assignment_path} is not a directory")
        return False
    for tgt in (".tmcproject.yml", "test", "src", "tmc"):
        if not any(filepath.name == tgt for filepath in assignment_path.iterdir()):
            logging.debug(f"{assignment_path} is not a TMC assignment (missing {tgt})")
            return False
    logging.debug(f"{assignment_path} is a valid TMC assignment")
    return True


def update_course(course_path: Path) -> None:
    course_path = course_path.resolve()
    logging.info(f"Updating TMC-python-tester for course {course_path}")
    download_tmc_python_tester(course_path, update=True)
    is_valid_course(course_path)
    for maybe_part in course_path.iterdir():
        logging.debug(f"Checking whether {maybe_part} is a course part")
        if not is_valid_part(maybe_part):
            logging.debug("Not a part, skipping")
            continue
        for maybe_assignment in maybe_part.iterdir():
            logging.debug(f"Checking whether {maybe_assignment} is an assignment")
            if not is_valid_assignment(maybe_assignment):
                logging.debug("Not an assignment, skipping")
                continue
            logging.info(f"Updating assignment at {maybe_assignment}")
            create_tmc_dir(maybe_assignment)


@dataclass
class TestTask:
    path: Path

    @property
    def course_path(self) -> Path:
        return self.path.parent.parent

    @property
    def part_path(self) -> Path:
        return self.path.parent


@dataclass
class TestResult:
    task: TestTask
    success: bool
    stdout: str
    stderr: str


def collect_tasks(paths: list[Path]) -> Generator[TestTask, None, None]:
    paths = [p.resolve() for p in paths]
    for path in paths:
        if is_valid_assignment(path):
            logging.debug(f"{path} is assignment")
            yield TestTask(path)
        elif is_valid_part(path):
            logging.debug(f"{path} appears to be a part")
            yield from collect_tasks(
                list(child for child in path.iterdir() if child.is_dir())
            )
        elif is_valid_course(path):
            logging.debug(f"{path} appears to be a course")
            yield from collect_tasks(
                list(child for child in path.iterdir() if child.is_dir())
            )
        else:
            logging.debug(f"{path} is neither an assignment, a part, or a course")


def is_last_child_of_parent(nodeid: object, tree: treelib.Tree) -> bool:
    if not tree.parent(nodeid):
        return True

    # variable needed for mypy; treelib is untyped, so otherwise the result
    # of this __eq__ is Any
    result: bool = (
        tree.get_node(nodeid) == tree.children(tree.parent(nodeid).identifier)[-1]
    )
    return result


def print_test_output(results: list[TestResult]) -> None:
    tree = treelib.Tree()
    tree.create_node("Test Results", "root")

    for course_path in set(result.task.course_path for result in results):
        tree.create_node(course_path.name, course_path, parent="root")

    for part_path in set(result.task.part_path for result in results):
        tree.create_node(part_path.name, part_path, parent=part_path.parent)

    for idx, result in enumerate(results):
        affix = (
            "\x1b[32;1mSUCCESS\x1b[0m" if result.success else "\x1b[31;1mFAIL\x1b[0m"
        )
        tree.create_node(
            f"{result.task.path.name} - {affix}",
            result.task.path,
            parent=result.task.part_path,
        )

    tree.show()


def test(paths: list[Path], detailed: bool = False) -> tuple[bool, list[TestResult]]:
    paths = [p.resolve() for p in paths]
    logging.debug("Collecting assignments")
    tasks: list[TestTask] = list(collect_tasks(paths))

    results: list[TestResult] = []
    logging.debug("Running tests")
    for task in tqdm(
        tasks, unit=" assg", disable=not logging.getLogger().isEnabledFor(logging.INFO)
    ):
        results.append(run_test_task(task))

    for result in results:
        if detailed or not result.success:
            logging.info("")
            logging.info(f"\nTEST RESULTS FOR {result.task.path}:")
            tabbed_stderr = "\n".join(
                "\t" + line for line in result.stderr.splitlines()
            )
            logging.info(tabbed_stderr)
    logging.info("\n")

    all_passed = all(result.success for result in results)
    if logging.getLogger().isEnabledFor(logging.INFO) or detailed:
        print_test_output(results)
    if all_passed:
        logging.info("\x1b[32;1mALL TEST PASSED\x1b[0m")
    else:
        logging.warning("\x1b[31;1mSOME TESTS FAILED\x1b[0m")

    return all_passed, results


@contextlib.contextmanager
def cwd(path: Path) -> Generator[None, None, None]:
    old_wd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_wd)


def run_test_task(task: TestTask) -> TestResult:
    assignment_path = task.path.resolve()
    logging.debug(f"Running tests for {assignment_path}")
    if not is_valid_assignment(assignment_path):
        raise ValueError(f"{assignment_path} is not a valid TMC assignment")
    with cwd(assignment_path):
        logging.debug(f"{assignment_path=}, {os.getcwd()=}")
        result = subprocess.run(
            ["python3", "-m", "tmc"],
            cwd=assignment_path,
            capture_output=True,
            text=True,
        )
    logging.debug(f"Test run complete; {result.returncode=}")
    return TestResult(task, result.returncode == 0, result.stdout, result.stderr)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        "tmc-course",
        description="Helper for building TestMyCode python programming courses",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=importlib.metadata.version(__package__ or __name__),
    )

    verbosity_grp = parser.add_mutually_exclusive_group()
    verbosity_grp.add_argument(
        "--quiet", "-q", action="store_true", help="Only output warning"
    )
    verbosity_grp.add_argument(
        "--debug", "-d", action="store_true", help="Output debugging information"
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
        "path", type=str, nargs="+", help="Path(s) of the new course(s)"
    )

    # INIT PART
    init_part_grp = init_actions.add_parser("part", help="Initialize a new course part")
    init_part_grp.add_argument(
        "path", type=str, nargs="+", help="Path(s) of the new part(s)"
    )

    # INIT ASSIGNMENT
    init_assignment_grp = init_actions.add_parser(
        "assignment", help="Initialize a assignment"
    )
    init_assignment_grp.add_argument(
        "path", type=str, nargs="+", help="Path(s) of the new assignment(s)"
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
    test_grp.add_argument(
        "path", type=str, nargs="+", help="Path(s) to test (course, part or assignment)"
    )
    test_grp.add_argument(
        "--details", action="store_true", help="Show more details about test results"
    )

    # UPDATE
    update_grp = actions.add_parser(
        "update", help="Update TMC-python-runner embedded in assignments"
    )
    update_grp.add_argument("path", type=str, help="Course root directory")

    # Parse arguments
    args = parser.parse_args(argv)

    # Verbosity control
    if not (args.quiet or args.debug):
        logging.basicConfig(format="%(message)s", level=logging.INFO)
    if args.quiet:
        logging.basicConfig(format="%(message)s", level=logging.WARNING)
    if args.debug:
        logging.basicConfig(
            format="%(levelname)s:%(asctime)s: %(message)s", level=logging.DEBUG
        )

    try:
        if args.action == "init":
            paths = (Path(path) for path in args.path)
            if args.init_action == "course":
                for path in paths:
                    init_course(path)
            elif args.init_action == "part":
                for path in paths:
                    init_part(path.parent, path.name)
            else:  # args.init_action == "assignment"
                language: Literal["fi", "en"] = "fi" if args.finnish else "en"
                for path in paths:
                    init_assignment(
                        path.parent.parent, path.parent.name, path.name, language
                    )
        if args.action == "test":
            all_passed, _ = test(
                [Path(path) for path in args.path], detailed=args.details
            )
            if not all_passed:
                return 1
        if args.action == "update":
            update_course(Path(args.path))
    except ActionCancelledException:
        print("OK, quitting")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
