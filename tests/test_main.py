import unittest
from scale_changer.main import ScaleChanger

class TestScaleChanger(unittest.TestCase):

    def setUp(self):
        self.scale_changer = ScaleChanger()

    def test_scale_up(self):
        result = self.scale_changer.scale_up(2)
        self.assertEqual(result, 4)  # Example expected result

    def test_scale_down(self):
        result = self.scale_changer.scale_down(2)
        self.assertEqual(result, 1)  # Example expected result

    def test_invalid_scale(self):
        with self.assertRaises(ValueError):
            self.scale_changer.scale_up(-1)

if __name__ == '__main__':
    unittest.main()