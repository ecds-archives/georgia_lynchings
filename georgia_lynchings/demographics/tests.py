from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from georgia_lynchings.demographics.models import Population

class PopulationTest(TestCase):
	fixtures = ['demographics.json']

	def setUp(self):
		self.ppl = Population.objects.get(id=1979)

	def test_literate_white(self):
		"""
		Tests the statewide totals function for a county.
		"""
		expected = 2930L
		actual = self.ppl.literate_white
		self.assertEqual(expected, actual) 

	def test_literate_black(self):
		expected = 3872L
		actual = self.ppl.literate_black
		self.assertEqual(expected, actual)

	def test_percent_white(self):
		expected = 38.65
		actual = self.ppl.percent_white
		self.assertAlmostEqual(expected, actual, places=2)

	def test_percent_black(self):
		expected = 61.32
		actual = self.ppl.percent_black
		self.assertAlmostEqual(expected, actual, places=2)

	def test_white_percent_literate(self):
		expected = 96.96
		actual = self.ppl.white_percent_literate
		self.assertAlmostEqual(expected, actual, places=2)

	def test_black_percent_literate(self):
		expected = 80.77
		actual = self.ppl.black_percent_literate
		self.assertAlmostEqual(expected, actual, places=2)