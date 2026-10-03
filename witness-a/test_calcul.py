import unittest

from calcul import addition
from calcul import multiplication


class CalculTest(unittest.TestCase):
    def test_addition(self) -> None:
        self.assertEqual(addition(2, 3), 5)

    def test_multiplication(self) -> None:
        self.assertEqual(multiplication(6, 7), 42)


if __name__ == "__main__":
    unittest.main()
