import unittest

from calcul import addition
from calcul import multiplication


class TestCalcul(unittest.TestCase):
    def test_addition(self) -> None:
        self.assertEqual(addition(4, 5), 9)

    def test_multiplication(self) -> None:
        self.assertEqual(multiplication(6, 7), 42)


if __name__ == "__main__":
    unittest.main()
