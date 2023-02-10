import unittest

from tmc import points
from tmc.utils import check_source, load, load_module

exercise = "src.solution"


@points("valid_assignment_en")
class SolutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module(exercise, "en")

    def test_0_main_ok(self):
        ok, line = check_source(self.module)
        self.assertTrue(
            ok,
            (
                "Extra code for testing should reside within the \n"
                'if __name__ == "__main__":\n'
                "block. The following line must be moved:\n"
                "{line}"
            ),
        )

    def test_1(self):
        funktio = load(exercise, "funktio", "en")
        self.assertEquals(
            1, funktio(), "The function 'function' should return the value 1"
        )


if __name__ == "__main__":
    unittest.main()
