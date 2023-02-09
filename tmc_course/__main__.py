import argparse
import logging
from pathlib import Path
from typing import Literal

from .tmc_course import UserExitException, init_assignment, init_course, init_part


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

    init_grp = actions.add_parser(
        "init", help="Initialize a new course, part or assignment"
    )
    init_actions = init_grp.add_subparsers(
        dest="init_action", required=True, metavar="TYPE"
    )

    init_course_grp = init_actions.add_parser("course", help="Initialize a new course")
    init_course_grp.add_argument(
        "course_path", type=str, help="Course root directory (should not exist)"
    )

    init_part_grp = init_actions.add_parser("part", help="Initialize a new course part")
    init_part_grp.add_argument("course_path", type=str, help="Course root directory")
    init_part_grp.add_argument(
        "part", type=str, nargs="+", help="Name(s) of part(s) to initialize"
    )

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

    args = parser.parse_args(argv)

    if not (args.quiet or args.verbose):
        logging.basicConfig(format="%(message)s", level=logging.INFO)
    if args.quiet:
        logging.basicConfig(format="%(message)s", level=logging.WARNING)
    if args.verbose:
        logging.basicConfig(
            format="%(levelname)s:%(asctime)s: %(message)s", level=logging.DEBUG
        )

    try:
        if args.action == "init":
            if args.init_action == "course":
                init_course(Path(args.course_path))
            elif args.init_action == "part":
                for part in args.part:
                    init_part(Path(args.course_path), part)
            elif args.init_action == "assignment":
                language: Literal["fi", "en"] = "fi" if args.finnish else "en"
                for assignment in args.assignment:
                    init_assignment(
                        Path(args.course_path), args.part, assignment, language
                    )
    except UserExitException:
        print("OK, quitting")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
