import json
from itertools import chain
from unittest import TestLoader, TextTestRunner

from .points import _name_test, _parse_points
from .result import TMCResult


class TMCTestRunner(TextTestRunner):
    """A test runner for TMC exercises."""

    resultclass = TMCResult

    def __init__(self, *args, **kwargs):
        super(TMCTestRunner, self).__init__(*args, **kwargs)

    def run(self, test):
        print("Running tests with some TMC magic...")
        return super(TMCTestRunner, self).run(test)

    def available_points(self):
        testLoader = TestLoader()
        tests = testLoader.discover(".", "test*.py", None)
        try:
            tests = list(chain(*chain(*tests._tests)))
        except Exception as error:
            print("Received following Exception:", error)
            tests.debug()

        points = map(_parse_points, tests)
        names = map(_name_test, tests)

        result = dict(zip(names, points))

        with open(".available_points.json", "w") as f:
            json.dump(result, f, ensure_ascii=False)
