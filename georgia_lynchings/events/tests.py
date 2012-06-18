import json
import logging
import rdflib
from mock import patch, MagicMock
from rdflib import Literal, URIRef
from pprint import pprint

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

from georgia_lynchings.events.models import MacroEvent, Event, \
    SemanticTriplet, Participant, Participant_S, Participant_O, Victim, \
    Individual
from georgia_lynchings.rdf.ns import dcx
from georgia_lynchings.rdf.queryset import QuerySet
from georgia_lynchings.rdf.sparqlstore import SparqlStore

logger = logging.getLogger(__name__)

class EventsAppTest(TestCase):
    def setUp(self):
        self.client = Client()  
        # override settings
        self.sparql_store_api_orig = settings.SPARQL_STORE_API
        settings.SPARQL_STORE_API = settings.TEST_SPARQL_STORE_API
        self.sparql_store_repo_orig = settings.SPARQL_STORE_REPOSITORY
        settings.SPARQL_STORE_REPOSITORY = settings.TEST_SPARQL_STORE_REPOSITORY
        
        # some handy fixtures from test data
        self.NONEXISTENT_MACRO_ID = '0'
        self.CRISP_MACRO_ID = '3' 
        self.RANDOLPH8_MACRO_ID = '8'
        self.PULASKI_MACRO_ID = '10'
        self.SAM_HOSE_MACRO_ID = '12'
        self.MERIWETHER_MACRO_ID = '25'        
        self.BROOKS_MACRO_ID = '57'        
        self.RANDOLPH_MACRO_ID = '208'        
        self.CAMPBELL_MACRO_ID = '360'

        self.EVENT_ID = '552'
        self.TRIPLET_ID = '571'
        self.PARTICIPANT_ID = '584'
        self.INDIVIDUAL_ID = '47767'
        
        self.VICTIM_E_COOPER_ID = '135239'   # Eli Cooper
        self.VICTIM_C_ROBERSON_ID = '135165' # John Henry Pinkney

    def tearDown(self):
        # restore settings
        settings.SPARQL_STORE_API = self.sparql_store_api_orig
        settings.SPARQL_STORE_REPOSITORY = self.sparql_store_repo_orig 
            

class MacroEventTest(EventsAppTest):
    def test_basic_rdf_properties(self):
        # For now, just test that the MacroEvent class has a few basic
        # properties. These properties don't mean much quite yet, so as this
        # property-interpretation code is fleshed out these tests will
        # likely grow to test something more meaningful.
        self.assertTrue('setup_Complex.csv#name-Macro_Event' in unicode(MacroEvent.rdf_type))

        macro = MacroEvent(self.SAM_HOSE_MACRO_ID)
        self.assertEqual('Coweta', macro.label)

    def test_objects(self):
        self.assertTrue(isinstance(MacroEvent.objects.all(), QuerySet))
        self.assertEqual(MacroEvent.objects.events.all().result_class, Event)
        self.assertEqual(MacroEvent.objects.events.triplets.participants.all().result_class, Participant)

        macro = MacroEvent(self.SAM_HOSE_MACRO_ID)
        participants = list(macro.objects.events.triplets.participants)
        part_ids = set(int(part.id) for part in participants)
        self.assertIn(4542, part_ids)
        self.assertIn(14789, part_ids)
        self.assertIn(137531, part_ids)                               

        with patch.object(SparqlStore, 'query') as mock_query:
            mock_query.return_value=[
                {'result': 'http://example.com/#r1', 'gender': 'male'},
                {'result': 'http://example.com/#r2', 'gender': 'female'},
                {'result': 'http://example.com/#r3', 'gender': 'other'},
                {'result': 'http://example.com/#r4'},
            ]

            # if we specify .fields() and then access only those fields, the
            # values are prefetched by the initial query, and no additional
            # queries are necessary.
            individuals = list(macro.objects.events.triplets.participants.individuals.fields('gender'))
            genders = [i.gender for i in individuals]
            self.assertEqual(len(mock_query.call_args_list), 1)


class EventTest(EventsAppTest):
    # some fields on Event are unused but listed for later reference. for
    # now test only the ones we actually use
    def test_basic_rdf_properties(self):
        event = Event(self.EVENT_ID)
        self.assertEqual(event.event_type, 'murder')

    def test_related_object_properties(self):
        event = Event(self.EVENT_ID)
        
        # macro_event
        self.assertTrue(isinstance(event.macro_event, MacroEvent))
        self.assertEqual(event.macro_event.id, '1')
        self.assertEqual(event.macro_event.label, 'Houston')


class SemanticTripletTest(EventsAppTest):
    # some fields on SemanticTriplet are unused but listed for later
    # reference. for now test only the ones we actually use
    def test_related_object_properties(self):
        triplet = SemanticTriplet(self.TRIPLET_ID)

        # participants
        self.assertEqual(len(triplet.participant_s), 1)
        self.assertEqual(triplet.participant_s[0].id, '572')
        self.assertTrue(isinstance(triplet.participant_s[0], Participant))
        self.assertTrue(isinstance(triplet.participant_s[0], Participant_S))

        self.assertEqual(len(triplet.participant_o), 1)
        self.assertEqual(triplet.participant_o[0].id, '584')
        self.assertTrue(isinstance(triplet.participant_o[0], Participant))
        self.assertTrue(isinstance(triplet.participant_o[0], Participant_O))

        self.assertEqual(len(triplet.participants), 2)
        self.assertEqual(triplet.participants[0].id, '572')
        self.assertEqual(triplet.participants[1].id, '584')
        self.assertTrue(isinstance(triplet.participants[0], Participant))

        # event
        self.assertTrue(isinstance(triplet.event, Event))
        self.assertEqual(triplet.event.id, '552')
        self.assertEqual(triplet.event.label, 'murder (near fort valley)')

        # macro_event
        self.assertTrue(isinstance(triplet.macro_event, MacroEvent))
        self.assertEqual(triplet.macro_event.id, '1')
        self.assertEqual(triplet.macro_event.label, 'Houston')


class IndividualTest(EventsAppTest):
    def test_data_properties(self):
        individual = Individual(self.INDIVIDUAL_ID)

        self.assertEqual(individual.actor_name, 'colored')
        self.assertEqual(individual.last_name, 'Walker')
        self.assertEqual(individual.gender, 'male')

    def test_related_object_properties(self):
        individual = Individual(self.INDIVIDUAL_ID)
        self.assertEqual(individual.participant.id, self.PARTICIPANT_ID)
        
        
class VictimTest(EventsAppTest):
    # some fields on Victim are unused but listed for later reference. for
    # now test only the ones we actually use
    def test_basic_rdf_properties(self):
        victim = Victim(self.VICTIM_E_COOPER_ID)
        self.assertEqual(victim.primary_name, 'Eli Cooper')
        self.assertEqual(victim.primary_alleged_crime, 'Organizing Black Farmers')
        self.assertEqual(victim.primary_county, 'Laurens')        

    def test_related_object_properties(self):
        victim = Victim(self.VICTIM_E_COOPER_ID)
        
        # macro_event
        self.assertTrue(isinstance(victim.macro_event, MacroEvent))
        self.assertEqual(victim.macro_event.id, '108')
        self.assertEqual(victim.macro_event.label, 'Laurens') 
        
    def test_macro_event_victims(self):
        # This macro event has 1 victims       
        victim1 = Victim(self.VICTIM_C_ROBERSON_ID)
        self.assertEqual(victim1.primary_name, 'Curry Roberson')

        macro = MacroEvent(self.PULASKI_MACRO_ID)
        self.assertEqual(victim1.id, macro.victims[0].id)                       
                
class ViewsTest(EventsAppTest):

    def test_macro_events_url(self):
        # times_url = '/events/'        
        macro_events_url = reverse('events:macro_events')       
        macro_events_response = self.client.get(macro_events_url)       
        
        expected, got = 200, macro_events_response.status_code
        self.assertEqual(expected, got, 'Expected %s status code, got %s' % (expected, got))
        context_events = macro_events_response.context['events']
        self.assertGreater(len(list(context_events)), 325, 
            'Expected len is greater than 325 but returned %s for results' % (len(list(context_events)))) 
          
        # test type of macro event label, should be literal
        self.assertTrue(isinstance(macro_events_response.context['events'][0].label, Literal),
                        'Expected melabel type Literal')
        # test value of macro event label  for first item     
        expected, got = macro_events_response.context['events'][0].label[:7], u'Houston'
        msg = 'Expected macro event label [%s] but returned [%s] for results' % (expected, got)
        self.assertEqual(expected, got, msg)
        
    def test_map_json(self):
        json_url = reverse('events:map-victim-data')

        # make sure url returns correctly
        response = self.client.get(json_url)
        expected, got = 200, response.status_code
        self.assertEqual(expected, got,
                         "Should have gotten %s but got %s from url %s" %  (expected, got, json_url))

        #make sure it has the correct content type
        self.assertEqual(response['Content-Type'], 'application/json',
                         'Should have Content-Type application/json but has %s' % (response['Content-Type']))
        #make sure it is valid json - this will fail if json is invalid
        json.loads(response.content)
