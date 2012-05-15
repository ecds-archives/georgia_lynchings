from django.test import TestCase

from georgia_lynchings.lynchings.models import Accusation, Race, County, Story, Person, Alias, Lynching

class PersonTest(TestCase):
    def setUp(self):
        # Test for person with a name
        race = Race(label="african american")
        pn = {
            'pca_id': 934334,
            'name': 'John Doe',
            'race': race,
            'gender': 'M',
            'age': 42,
        }
        self.person_name = Person(**pn)
        self.person_name.save()

        # Test for person with no name.
        pnn = {
            'pca_id': 934335,
            'race': race,
            'gender': 'M',
            'age': 42,
            }
        self.person_noname = Person(**pnn)
        self.person_noname.save()

    def test_pretty_name(self):
        exp_pn = 'John Doe'
        actual = self.person_name.pretty_name
        self.assertEqual(exp_pn, actual)

        exp_pnn = 'Unknown african american Male'
        actual_pnn = self.person_noname.pretty_name
        self.assertEqual(exp_pnn, actual_pnn)

