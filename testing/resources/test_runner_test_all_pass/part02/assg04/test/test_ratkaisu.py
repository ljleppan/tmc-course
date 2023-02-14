import unittest

from tmc import points
from tmc.utils import check_source, load, load_module

exercise = "src.ratkaisu"


@points("valid_assignment_fi")
class RatkaisuTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module(exercise, "fi")

    def test_0_paaohjelma_kunnossa(self):
        ok, line = check_source(self.module)
        self.assertTrue(
            ok,
            (
                "Funktioita testaava koodi tulee sijoittaa lohkon\n"
                'if __name__ == "__main__":\n'
                "sisälle. Seuraava rivi tulee siirtää:\n"
                "{line}"
            ),
        )

    def test_1(self):
        funktio = load(exercise, "funktio", "fi")
        self.assertEquals(1, funktio(), "Funktion 'funktio' tulisi palauttaa arvo 1")


if __name__ == "__main__":
    unittest.main()
