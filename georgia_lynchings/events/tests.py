from django.test import TestCase
from georgia_lynchings.events.models import MacroEvent


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class MacroEventTest(TestCase):
    def test_basic_rdf_properties(self):
        # For now, just test that the MacroEvent class has a few basic
        # properties. These properties don't mean much quite yet, so as this
        # property-interpretation code is fleshed out these tests will
        # likely grow to test something more meaningful.
        self.assertTrue('setup_Complex.csv#r' in unicode(MacroEvent.rdf_type))
        self.assertTrue('data_Complex.csv#Identifier' in unicode(MacroEvent.label))

        self.assertTrue('setup_xref_Complex-Complex.csv#r' in unicode(MacroEvent.events))

        self.assertTrue('setup_Simplex.csv#r' in unicode(MacroEvent.county))
        self.assertTrue('setup_Simplex.csv#r' in unicode(MacroEvent.victim))
        self.assertTrue('setup_Simplex.csv#r' in unicode(MacroEvent.case_number))
        self.assertTrue('setup_Simplex.csv#r' in unicode(MacroEvent.verified_semantic))
        self.assertTrue('setup_Simplex.csv#r' in unicode(MacroEvent.verified_details))
        self.assertTrue('setup_Simplex.csv#r' in unicode(MacroEvent.last_coded))
