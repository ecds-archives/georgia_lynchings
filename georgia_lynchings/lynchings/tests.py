from datetime import date
from django.test import TestCase

from georgia_lynchings.lynchings.models import Accusation, Race, County, Story, Person, Alias, Lynching

class PersonTest(TestCase):
    def setUp(self):
        # Test for person with a name
        race = Race(label="african american")
        race.save()

        # Test for person with no name.
        prsn = {
            'pca_id': 934335,
            'race': race,
            'age': 42,
            }
        self.person = Person(**prsn)
        self.person.save()

    def test_pretty_name(self):

        self._name_tester(self.person, 'Unknown Person')

        self.person.gender = 'M'
        self.person.save()
        self._name_tester(self.person, 'Unknown african american Male')

        self.person.name = 'John Doe'
        self.person.save()
        self._name_tester(self.person, 'John Doe')

    def _name_tester(self, person, exp_name):
        self.assertEqual(exp_name, person.pretty_name)

class StoryTest(TestCase):

    fixtures = ['test_lynchings.json']

    def test_pretty_string(self):
        story = Story.objects.get(pk=2)
        exp = 'Lynching of Unknown Person, Unknown race 1 Female in 1907, 1899'
        lynching = Lynching.objects.get(pk=2)
        lynching.date = date(1907, 7, 3)
        lynching.save()
        self.assertEqual(exp, story.pretty_string)


    def test_county_list(self):
        story = Story.objects.get(pk=2)
        self.assertEqual(len(story.county_list), 5)

    def test_year(self):
        story = Story.objects.get(pk=2)
        self.assertEqual(story.year, 1899)
        lynching = Lynching.objects.get(pk=2)
        lynching.date = date(1907, 7, 3)
        lynching.save()
        self.assertEqual(story.year, 1907)

