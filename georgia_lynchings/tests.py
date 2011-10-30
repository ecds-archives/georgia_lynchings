import unittest
from django.conf import settings

class TestSettings(unittest.TestCase):

    def setUp(self):
        print "test setUp\n" % self.settings.STATIC_URL

    def test_css(self):
        self.assertEqual(10, 10, "Not 10")

if __name__ == '__main__':

    unittest.main()
