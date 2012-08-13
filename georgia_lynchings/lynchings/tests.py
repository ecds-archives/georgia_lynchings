from datetime import date

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from georgia_lynchings.lynchings.models import Accusation, Race, \
    County, Victim, Lynching

accusation1 = {'label': 'Test Crime'}
race1 = {'label': "test race"}
named_victim = {
    'name': 'Test Victim',
    'gender': 'M',
    'date': date(1893, 02, 18),
    'detailed_reason':  'Is there ever one?'
}
unnamed_victim = {
    'gender': 'M',
    'date': date(1893, 02, 18),
    'detailed_reason':  'Is there ever one?'
}

class AccusationTest(TestCase):

    def setUp(self):
        self.acc = Accusation(label=accusation1["label"])
        self.acc.save()

    def test_string(self):
        expected = "Test Crime"
        self.assertEqual(expected, "%s" % self.acc)

class RaceTest(TestCase):

    def setUp(self):
        self.race = Race(label=race1['label'])
        self.race.save()

    def test_string(self):
        expected = "test race"
        self.assertEqual(expected, "%s" % self.race)

class LynchingTest(TestCase):
    fixtures = ['demographics.json',]

    def setUp(self):
        # Setup other related objects
        county = County.objects.get(name="Decatur")
        acc = Accusation(**accusation1)
        acc.save()
        race = Race(**race1)
        race.save()

        #Lynching
        self.lynching = Lynching(pca_id="22394")
        self.lynching.save()

        # Named Victim
        self.victim1 = Victim(**named_victim)
        self.victim1.save()
        self.victim1.county = county
        self.victim1.accusation.add(acc)
        self.victim1.race = race
        self.victim1.lynching = self.lynching
        self.victim1.save()

        # Unnamed Victim
        self.victim2 = Victim(**unnamed_victim)
        self.victim2.save()
        self.victim2.county = county
        self.victim2.accusation.add(acc)
        self.victim2.race = race
        self.victim2.lynching = self.lynching
        self.victim2.save()

    def test_pretty_string(self):
        expected = "Lynching of Test Victim, Unknown test race Male in 1893"
        self.assertEqual(expected, self.lynching.pretty_string)

    def test_county_list(self):
        expected = "Decatur"
        county_names = [county.name for county in self.lynching.county_list]
        self.assertTrue(expected in county_names)

    def test_year(self):
        expected = 1893
        self.assertEqual(expected, self.lynching.year)
        self.victim2.date = date(1923, 02, 10)
        self.victim2.save()
        self.assertEqual(1923, self.lynching.year)

class VictimTest(TestCase):

    def setUp(self):
        self.victim = Victim()
        self.victim.save()

    def test_pretty_name(self):
        # Test no name at all
        self.assertEqual("Unknown Person", self.victim.pretty_name)
        # Add gender
        self.victim.gender = 'M'
        self.victim.save()
        self.assertEqual("Unknown Person", self.victim.pretty_name)
        # Add Race, should change.
        race = Race(label="Test Race")
        self.victim.race = race
        self.victim.save()
        self.assertEqual("Unknown Test Race Male", self.victim.pretty_name)
        # Add actual name
        self.victim.name = "Test Name"
        self.victim.save()
        self.assertEqual("Test Name", self.victim.pretty_name)


