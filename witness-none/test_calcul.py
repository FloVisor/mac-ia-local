import unittest

from calcul import addition
from calcul import soustraction


class TestCalcul(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(addition(2, 3), 5)

    def test_soustraction(self):
        self.assertEqual(soustraction(7, 2), 5)


if __name__ == "__main__":
    unittest.main()
