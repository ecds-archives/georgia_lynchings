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
    SemanticTriplet, Victim, get_filters
from georgia_lynchings.events.details import Details
from georgia_lynchings.events.timemap import Timemap, GeoCoordinates, \
    MacroEvent_Item
from georgia_lynchings.rdf.ns import dcx

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
        self.PULASKI_MACRO_ID = '10'                  
        self.SAM_HOSE_MACRO_ID = '12'
        self.MERIWETHER_MACRO_ID = '25'        
        self.BROOKS_MACRO_ID = '57'        
        self.RANDOLPH_MACRO_ID = '208'        
        self.CAMPBELL_MACRO_ID = '360'

        self.EVENT_ID = '552'
        self.TRIPLET_ID = '555'
        
        self.VICTIM_E_COOPER_ID = '135239'   # Eli Cooper
        self.VICTIM_JH_PINKNEY_ID = '135165' # John Henry Pinkney
        self.VICTIM_J_BUCHAN_ID = '136088'   # Jerry Buchan
        self.VICTIM_C_ROBERSON_ID = '136089' # Curry Roberson      

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

    def test_get_cities(self):
        macro = MacroEvent(self.SAM_HOSE_MACRO_ID)
        expected, got = [u'palmetto'], macro.get_cities() 
        self.assertEqual(expected, got, 'Expected %s city list, got %s' % (expected, got))
        
        macro = MacroEvent(self.NONEXISTENT_MACRO_ID)
        expected, got = [], macro.get_cities() 
        self.assertEqual(expected, got, 'Expected %s for nonexistant city macro id, got %s' % (expected, got))
        
    def test_get_date_range(self):
        macro = MacroEvent(self.CAMPBELL_MACRO_ID)
        datedict = macro.get_date_range()
        expected, got = u'1882-05-28', datedict['mindate'] 
        self.assertEqual(expected, got, 'Expected %s minimum date, got %s' % (expected, got))
        expected, got = u'1882-08-10', datedict['maxdate'] 
        self.assertEqual(expected, got, 'Expected %s maximum date, got %s' % (expected, got))
        
        macro = MacroEvent(self.NONEXISTENT_MACRO_ID)
        expected, got = None, macro.get_date_range() 
        self.assertEqual(expected, got, 'Expected %s for nonexistant date_range macro id, got %s' % (expected, got)) 
        
    def test_get_details(self):
        details = Details(self.BROOKS_MACRO_ID)
        result = details.get()      
        # Test article total for BROOKS dcx:r57 macro event 
        expected, got = '3', result['articleTotal'] 
        self.assertEqual(expected, got, 'Expected %s articleTotal, got %s' % (expected, got))
        # Test event_type for BROOKS dcx:r57 macro event         
        event_list, item = result['event_type'], 'lynching'
        self.assertIn(item, event_list, 'Expected %s event_type in event_list' % (item))
        # Test melabel for BROOKS dcx:r57 macro event 
        expected, got = 'Brooks', result['melabel'] 
        self.assertEqual(expected, got, 'Expected %s macro event label, got %s' % (expected, got))
        # Test evlabel for BROOKS dcx:r57 macro event         
        city_list, item = result['location'], 'barwick'
        self.assertIn(item, city_list, 'Expected %s city in city_list' % (item))        
        # Test mindate for BROOKS dcx:r57 macro event 
        expected, got = '1909-07-02', result['mindate'] 
        self.assertEqual(expected, got, 'Expected %s mindate, got %s' % (expected, got)) 
        # Test maxdate for BROOKS dcx:r57 macro event 
        expected, got = '1909-07-02', result['maxdate'] 
        self.assertEqual(expected, got, 'Expected %s maxdate, got %s' % (expected, got)) 
        # Test triplet_first for BROOKS dcx:r57 macro event 
        expected = 'mob hung (violence against people 7/2/1909 senatobia) negro (steven veasey male)'
        got = result['events'][0]['triplet_first'] 
        self.assertEqual(expected, got, 'Expected %s triplet_first, got %s' % (expected, got))
        
        # test get_me_articles
        expected, got = '3', details.get_me_articles() 
        self.assertEqual(expected, got, 'Expected %s articleTotal, got %s' % (expected, got))
                
        # test get_me_events
        evdict=[{u'event': rdflib.term.URIRef('http://galyn.example.com/source_data_files/data_Complex.csv#r19684'),
              u'evlabel': rdflib.term.Literal(u'lynching (senatobia)'),
              u'macro': rdflib.term.URIRef('http://galyn.example.com/source_data_files/data_Complex.csv#r57'),
              u'melabel': rdflib.term.Literal(u'Brooks')},
             {u'event': rdflib.term.URIRef('http://galyn.example.com/source_data_files/data_Complex.csv#r19811'),
              u'evlabel': rdflib.term.Literal(u'lynching (barwick)'),
              u'macro': rdflib.term.URIRef('http://galyn.example.com/source_data_files/data_Complex.csv#r57'),
              u'melabel': rdflib.term.Literal(u'Brooks')}]
              
        events = details.get_me_events(evdict)
        event_list, item = events['events'][1]['evlabel'], 'lynching (barwick)'
        self.assertIn(item, event_list, 'Expected %s in event_list' % (item))                 
                
        # test get_me_title
        got, expected = details.get_me_title(evdict), 'Brooks'
        self.assertEqual(expected, got, 'Expected %s title, got %s' % (expected, got))
                
        # test get_name
        got, expected = details.get_name('Firstname', 'Lastname'), 'Firstname Lastname'
        self.assertEqual(expected, got, 'Expected %s , got %s' % (expected, got))
        got, expected = details.get_name('Firstname', None), 'Firstname'
        self.assertEqual(expected, got, 'Expected %s , got %s' % (expected, got))
        got, expected = details.get_name(None, 'Lastname'), 'Lastname'
        self.assertEqual(expected, got, 'Expected %s , got %s' % (expected, got))
        got, expected = details.get_name(None, None), None
        self.assertEqual(expected, got, 'Expected %s , got %s' % (expected, got))                        
                
        # test update_me_participants
        results = {}
        results['events']=evdict
        details.update_me_participants(results,['uparto'])
        got, expected = results['events'][1]['uparto'][1]['role'], 'coroner'
        self.assertEqual(expected, got, 'Expected %s participant role, got %s' % (expected, got))
        
        # test update_me_triplets
        results = {}
        results['events']=evdict
        details.update_me_triplets(results)
        expected = 'mob hung (violence against people 7/2/1909 senatobia) negro (steven veasey male)'
        got = results['events'][0]['triplet_first']
        self.assertEqual(expected, got, 'Expected %s triplet, got %s' % (expected, got))        

        # Test participant-o for BROOKS dcx:r57 macro event 
        # parto age
        expected, got = 'young', result['events'][0]['uparto'][0]['age']
        self.assertEqual(expected, got, 'Expected %s qualitative age, got %s' % (expected, got))
        # parto gender
        expected, got = 'male', result['events'][0]['uparto'][0]['gender']
        self.assertEqual(expected, got, 'Expected %s gender, got %s' % (expected, got))
        # parto name
        expected, got = 'veasey', result['events'][0]['uparto'][0]['name']
        self.assertEqual(expected, got, 'Expected %s name, got %s' % (expected, got))
        # parto race
        expected, got = 'white', result['events'][0]['uparto'][0]['race']
        self.assertEqual(expected, got, 'Expected %s race, got %s' % (expected, got)) 
        # parts gender
        expected, got = 'female', result['events'][0]['uparts'][1]['gender']
        self.assertEqual(expected, got, 'Expected %s gender, got %s' % (expected, got))
        # parts role
        expected, got = 'sister', result['events'][0]['uparts'][1]['role']
        self.assertEqual(expected, got, 'Expected %s role, got %s' % (expected, got))
        
        # test get_me_victims
        results = details.get_me_victims()
        got, expected = results['victims'][0]['alleged_crime'], 'Attempted Theft'
        self.assertEqual(expected, got, 'Expected %s victim alleged crime, got %s' % (expected, got))  
        got, expected = results['victims'][0]['name'], 'Henry Isaac'
        self.assertEqual(expected, got, 'Expected %s victim name, got %s' % (expected, got)) 
        got, expected = results['victims'][0]['county'], 'Brooks'
        self.assertEqual(expected, got, 'Expected %s victim county, got %s' % (expected, got))
        got, expected = results['victims'][0]['lynching_date'], '1909-07-02'
        self.assertEqual(expected, got, 'Expected %s victim lynching date, got %s' % (expected, got))                                                         
  
        details = Details(self.MERIWETHER_MACRO_ID)
        result = details.get()
        event_list, item = result['event_type'], 'murder'
        self.assertIn(item, event_list, 'Expected %s event_type in event_list' % (item))
        outcome_list, item = result['outcome'], 'reward of 250$'
        self.assertIn(item, outcome_list, 'Expected %s outcome in outcome_list' % (item))         
        reason_list, item = result['reason'], 'capture of the negro'
        self.assertIn(item, reason_list, 'Expected %s reason in reason_list' % (item))  
        expected, got = 'Meriwether', result['melabel'] 
        self.assertEqual(expected, got, 'Expected %s articleTotal, got %s' % (expected, got))                                            

        details = Details(self.NONEXISTENT_MACRO_ID)
        expected, got = None, details.get() 
        self.assertEqual(expected, got, 'Expected %s for nonexistant date_range macro id, got %s' % (expected, got)) 
        
    def test_get_date_range(self):
        macro = MacroEvent(self.CAMPBELL_MACRO_ID)
        datedict = macro.get_date_range()
        expected, got = u'1882-05-28', datedict['mindate'] 
        self.assertEqual(expected, got, 'Expected %s minimum date, got %s' % (expected, got))
        expected, got = u'1882-08-10', datedict['maxdate'] 
        self.assertEqual(expected, got, 'Expected %s maximum date, got %s' % (expected, got))
        
        macro = MacroEvent(self.NONEXISTENT_MACRO_ID)
        expected, got = None, macro.get_date_range() 
        self.assertEqual(expected, got, 'Expected %s for nonexistant date_range macro id, got %s' % (expected, got))                  
        
    def test_get_triplets(self):
        macro = MacroEvent(self.SAM_HOSE_MACRO_ID)
        triplets = macro.get_triplets()
        self.assertEqual(10, len(triplets))
        match = triplets[0]
        self.assertTrue(str(match['event']).endswith('#r4538'))
        self.assertEqual(match['evlabel'], 'lynching law creation (columbia)')
        self.assertTrue(str(match['triplet']).endswith('#r4541'))
        self.assertTrue(match['trlabel'].startswith('state supreme court make law'))

    def test_get_triplets_by_event(self):
        macro = MacroEvent(self.SAM_HOSE_MACRO_ID)
        eventdict = macro.get_triplets_by_event()       
        expected, got = 2, len(eventdict[u'lynching law creation (columbia)'] )
        self.assertEqual(expected, got, 'Expected %s triplet length, got %s' % (expected, got))
        expected, got = 8, len(eventdict[ u'seeking of a negro (palmetto)'] )
        self.assertEqual(expected, got, 'Expected %s triplet length, got %s' % (expected, got))
        expected, got = u'mob lynch', eventdict[u'seeking of a negro (palmetto)'][1][:9] 
        self.assertEqual(expected, got, 'Expected %s triplet length, got %s' % (expected, got))                    
                
        macro = MacroEvent(self.NONEXISTENT_MACRO_ID)
        expected, got = {}, macro.get_triplets_by_event() 
        self.assertEqual(expected, got, 'Expected %s for nonexistant triplet macro id, got %s' % (expected, got)) 
                               
    def test_parto(self):
        macro = MacroEvent(self.RANDOLPH_MACRO_ID)
        resultSet = macro.get_statement_object_data()
        # Test macro event
        expected, got = 'Randolph', resultSet[7]['melabel']
        self.assertEqual(expected, got, 'Expected %s macro event, got %s' % (expected, got))        
        # Test name_of_indivd_actor
        expected, got = 'mother', resultSet[7]['name_of_indivd_actor']
        self.assertEqual(expected, got, 'Expected %s name_of_indivd_actor, got %s' % (expected, got))         
        # Test qualitative age
        expected, got = 'elderly', resultSet[7]['qualitative_age']
        self.assertEqual(expected, got, 'Expected %s qualitative_age, got %s' % (expected, got))
        # Test gender
        expected, got = 'female', resultSet[7]['gender']
        self.assertEqual(expected, got, 'Expected %s gender, got %s' % (expected, got)) 
        # Test lname
        expected, got = 'taylor', resultSet[0]['lname']
        self.assertEqual(expected, got, 'Expected %s lname, got %s' % (expected, got))
        # Test race
        expected, got = 'white', resultSet[0]['race']
        self.assertEqual(expected, got, 'Expected %s race, got %s' % (expected, got))
        # Test name_of_indivd_actor
        expected, got = 'sheriff', resultSet[0]['name_of_indivd_actor']
        self.assertEqual(expected, got, 'Expected %s name_of_indivd_actor, got %s' % (expected, got))
        
    def test_parts(self):
        macro = MacroEvent(self.CRISP_MACRO_ID)
        resultSet = macro.get_statement_subject_data()
        # Test macro event
        expected, got = 'Crisp', resultSet[7]['melabel']
        self.assertEqual(expected, got, 'Expected %s macro event, got %s' % (expected, got))        
        # Test name_of_indivd_actor
        expected, got = 'sheriff', resultSet[5]['name_of_indivd_actor']
        self.assertEqual(expected, got, 'Expected %s name_of_indivd_actor, got %s' % (expected, got))         
        # Test qualitative age
        expected, got = 'young', resultSet[7]['qualitative_age']
        self.assertEqual(expected, got, 'Expected %s qualitative_age, got %s' % (expected, got))
        # Test gender
        expected, got = 'male', resultSet[7]['gender']
        self.assertEqual(expected, got, 'Expected %s gender, got %s' % (expected, got)) 
        # Test lname
        expected, got = 'simmons', resultSet[7]['lname']
        self.assertEqual(expected, got, 'Expected %s lname, got %s' % (expected, got))
        # Test race
        expected, got = 'white', resultSet[7]['race']
        self.assertEqual(expected, got, 'Expected %s race, got %s' % (expected, got))
        # Test name_of_indivd_actor
        expected, got = 'coroner', resultSet[6]['name_of_indivd_actor']
        self.assertEqual(expected, got, 'Expected %s name_of_indivd_actor, got %s' % (expected, got))                                             

    def test_index_data(self):
        hose = MacroEvent(self.SAM_HOSE_MACRO_ID)
        hose_data = hose.index_data()

        self.assertEqual(hose_data['min_date'], '1899-12-04')
        self.assertEqual(hose_data['max_date'], '1899-12-04')

        self.assertEqual(len(hose_data['event_type']), 2)
        self.assertIn('lynching law creation', hose_data['event_type'])
        self.assertIn('seeking of a negro', hose_data['event_type'])                                

        self.assertEqual(len(hose_data['city']), 1)
        self.assertEqual(hose_data['city'][0], 'palmetto')

        self.assertEqual(len(hose_data['triplet_label']), 10)

        self.assertEqual(len(hose_data['participant_uri']), 5)
        self.assertEqual(hose_data['participant_uri'][0], dcx.r4586)
        self.assertEqual(len(hose_data['participant_last_name']), 5)
        self.assertEqual(hose_data['participant_last_name'][0], 'cranford')
        self.assertEqual(len(hose_data['participant_qualitative_age']), 0)
        self.assertEqual(len(hose_data['participant_race']), 1)
        self.assertEqual(hose_data['participant_race'][0], 'white')
        self.assertEqual(len(hose_data['participant_gender']), 7)
        self.assertEqual(hose_data['participant_gender'][0], 'male')
        self.assertEqual(len(hose_data['participant_actor_name']), 0)

        # test cases for fields that are empty in hose
        crisp = MacroEvent(self.CRISP_MACRO_ID)
        crisp_data = crisp.index_data()

        self.assertEqual(len(crisp_data['participant_qualitative_age']), 1)
        self.assertEqual(crisp_data['participant_qualitative_age'][0], 'young')
        self.assertEqual(len(crisp_data['participant_actor_name']), 3)
        self.assertEqual(crisp_data['participant_actor_name'][0], 'accomplice')


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

        # event
        self.assertTrue(isinstance(triplet.event, Event))
        self.assertEqual(triplet.event.id, '552')
        self.assertEqual(triplet.event.label, 'murder (near fort valley)')

        # macro_event
        self.assertTrue(isinstance(triplet.macro_event, MacroEvent))
        self.assertEqual(triplet.macro_event.id, '1')
        self.assertEqual(triplet.macro_event.label, 'Houston')
    
    def test_index_data(self):
        triplet = SemanticTriplet(self.TRIPLET_ID)
        idata = triplet.index_data()

        self.assertEqual(idata['row_id'], '555')
        self.assertTrue(idata['uri'].endswith('#r555'))
        self.assertTrue(idata['complex_type'].endswith('Semantic_Triplet'))
        self.assertTrue(idata['label'].startswith('party (male unknown armed)'))
        self.assertTrue(idata['macro_event_uri'].endswith('#r1'))
        
class VictimTest(EventsAppTest):
    # some fields on Victim are unused but listed for later reference. for
    # now test only the ones we actually use
    def test_basic_rdf_properties(self):
        victim = Victim(self.VICTIM_E_COOPER_ID)
        self.assertEqual(victim.victim_name, 'Eli Cooper')
        self.assertEqual(victim.victim_alleged_crime, 'Organizing Black Farmers')
        self.assertEqual(victim.victim_county_of_lynching, 'Laurens')        

    def test_related_object_properties(self):
        victim = Victim(self.VICTIM_E_COOPER_ID)
        
        # macro_event
        self.assertTrue(isinstance(victim.macro_event, MacroEvent))
        self.assertEqual(victim.macro_event.id, '108')
        self.assertEqual(victim.macro_event.label, 'Laurens') 
        
    def test_index_data(self):
        victim = Victim(self.VICTIM_E_COOPER_ID)
        idata = victim.index_data()

        self.assertEqual(idata['row_id'], '135239')
        self.assertTrue(idata['uri'].endswith('#r135239'))
        self.assertTrue(idata['complex_type'].endswith('Victim'))
        self.assertTrue(idata['label'].startswith('Laurens'))
        self.assertTrue(idata['macro_event_uri'].endswith('#r108'))

    def test_macro_event_victims(self):
        # This macro event has 3 victims        
        victim1 = Victim(self.VICTIM_JH_PINKNEY_ID)
        self.assertEqual(victim1.victim_name, 'John Henry Pinkney')
        victim2 = Victim(self.VICTIM_J_BUCHAN_ID)
        self.assertEqual(victim2.victim_name, 'Jerry Buchan')
        victim3 = Victim(self.VICTIM_C_ROBERSON_ID)
        self.assertEqual(victim3.victim_name, 'Curry Roberson')

        macro = MacroEvent(self.PULASKI_MACRO_ID)
        self.assertEqual(victim1.id, macro.victims[0].id)
        self.assertEqual(victim2.id, macro.victims[1].id)
        self.assertEqual(victim3.id, macro.victims[2].id)                        
                
class ViewsTest(EventsAppTest):

    def test_get_articles_bogus_rowid(self):
        row_id = self.NONEXISTENT_MACRO_ID
        title = 'No records found'
        # articles_url = '/events/0/articles/'        
        articles_url = reverse('events:articles', kwargs={'row_id': row_id})
        articles_response = self.client.get(articles_url)
        expected, got = 200, articles_response.status_code  
        self.assertEqual(expected, got, 'Expected %s status code, got %s' % (expected, got))                  
        self.assertEqual(row_id, articles_response.context['row_id'], 
            'Expected %s but returned %s for row_id' % (row_id, articles_response.context['row_id']))
        self.assertEqual(0, len(articles_response.context['resultSet']), 
            'Expected len 0 but returned %s for resultSet' % (len(articles_response.context['resultSet'])))
        self.assertEqual(title, articles_response.context['title'], 
            'Expected %s but returned %s for title' % (row_id, articles_response.context['title']))

    def test_articles_url(self):
        row_id = self.SAM_HOSE_MACRO_ID
        title = 'Coweta'
        # articles_url = '/events/12/articles/'        
        articles_url = reverse('events:articles', kwargs={'row_id': row_id})
        articles_response = self.client.get(articles_url)
        expected, got = 200, articles_response.status_code
        self.assertEqual(expected, got, 'Expected %s status code, got %s' % (expected, got))
        self.assertEqual(row_id, articles_response.context['row_id'], 
            'Expected %s but returned %s for row_id' % (row_id, articles_response.context['row_id']))
        self.assertEqual(4, len(articles_response.context['resultSet']), 
            'Expected len 4 but returned %s for resultSet' % (len(articles_response.context['resultSet'])))
        self.assertEqual(title, articles_response.context['title'][:6], 
            'Expected %s but returned %s for title' % (row_id, articles_response.context['title'][:6]))


        for article in articles_response.context['resultSet']:
            self.assertTrue('\\' not in article['docpath_link'])

    def test_macro_events_url(self):
        # times_url = '/events/'        
        macro_events_url = reverse('events:macro_events')       
        macro_events_response = self.client.get(macro_events_url)       
        
        expected, got = 200, macro_events_response.status_code
        self.assertEqual(expected, got, 'Expected %s status code, got %s' % (expected, got))
        self.assertGreater(len(macro_events_response.context['results']), 325, 
            'Expected len is greater than 325 but returned %s for results' % (len(macro_events_response.context['results']))) 
          
        # test type of macro event label, should be literal
        self.assertTrue(isinstance(macro_events_response.context['results'][0]['melabel'], Literal),
                        'Expected melabel type Literal')
        # test value of macro event label  for first item     
        expected, got = macro_events_response.context['results'][0]['melabel'][:7], u'Houston'
        msg = 'Expected macro event label [%s] but returned [%s] for results' % (expected, got)
        self.assertEqual(expected, got, msg)
        
        # test value of article count for first item       
        expected, got = macro_events_response.context['results'][0]['articleTotal'], u'3'
        msg = 'Expected macro event article count [%s] but returned [%s] for results' % (expected, got)
        self.assertEqual(expected, got, msg)

    @patch('sunburnt.SolrInterface')
    def test_search_url(self, mock_solr_interface):
        mocksolr = MagicMock()
        mock_solr_interface.return_value = mocksolr
        mocksolr.query.return_value = mocksolr
        mocksolr.filter.return_value = mocksolr
        mocksolr.boost_relevancy.return_value = mocksolr
        solr_result = mocksolr.execute.return_value

        search_url = reverse('events:search')
        response = self.client.get(search_url, {'q': 'coweta'})
        self.assertContains(response, 'search results for')
        self.assertEqual(response.context['term'], 'coweta')
        self.assertEqual(response.context['results'], solr_result)
        self.assertTrue('form' in response.context)

    @patch('sunburnt.SolrInterface', new_callable=MagicMock)
    def test_advanced_search_url(self, mock_solr_interface):
        search_url = reverse('events:advanced_search')

        # for now just verify that we can get the advanced search page
        response = self.client.get(search_url)
        self.assertEqual(200, response.status_code)

    @patch('sunburnt.SolrInterface')
    def test_map_json(self, mock_solr_interface):
        mocksolr = MagicMock()
        mock_solr_interface.return_value = mocksolr
        mocksolr.query.return_value = mocksolr
        mocksolr.filter.return_value = mocksolr
        mocksolr.boost_relevancy.return_value = mocksolr
        solr_result = mocksolr.execute.return_value

        json_url = reverse('events:map-json')

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


class TimemapTest(TestCase):
    def setUp(self):
        # No filters
        self.tmap = Timemap()
        
        # Filters
        self.filters = [
            { 
                'title': 'Alleged Crime',
                'name': 'victim_allegedcrime_brundage',
                'prefix': 'ac_',
                # example of tags tuple (display name, slug, frequency):
                # 'tags': [
                #   ('Argument', 'ac_argument', 4), 
                #   ('Debt Dispute', 'ac_debt_dispute', 7), 
                #   ('Kidnapping/Theft', 'ac_kidnapping/theft', 17)
                # ]  
            }
        ]       
        self.tmapfilter = Timemap(self.filters) 
                 
        self.metadata = [
{u'label': rdflib.term.Literal(u'Crisp'),
 u'macro': rdflib.term.URIRef('http://galyn.example.com/source_data_files/data_Complex.csv#r3'),
 u'max_date': rdflib.term.Literal(u'1918-05-23', datatype=rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#date')),
 u'min_date': rdflib.term.Literal(u'1918-05-23', datatype=rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#date')),
 u'vcounty_brdg': rdflib.term.Literal(u'Crisp'),
 u'victim_allegedcrime_brundage': rdflib.term.Literal(u'Assault')},    
{u'label': rdflib.term.Literal(u'Attempted rape   & 10/30/1890   & Lowndes'),
 u'macro': rdflib.term.URIRef('http://galyn.example.com/source_data_files/data_Complex.csv#r5'),
 u'max_date': rdflib.term.Literal(u'1890-10-31', datatype=rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#date')),
 u'min_date': rdflib.term.Literal(u'1890-10-31', datatype=rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#date')),
 u'vcounty_brdg': rdflib.term.Literal(u'Lowndes'),
 u'victim_allegedcrime_brundage': rdflib.term.Literal(u'Debt Dispute')}
        ]
        
        self.item = {'label': 'Debt Dispute', 
                'row_id': '3',
                'max_date': '1896-06-02',
                'min_date': '1896-06-01', 
                'county': 'Muscogee',
                'victim_allegedcrime_brundage': ['Assault']}     
        
    def test_init(self):
        self.assertEqual(self.tmap.filters, []) 
        self.assertEqual(self.tmapfilter.filters, self.filters)             
        
    def test_timemap_format(self):
        result = self.tmap.format(self.metadata)
        self.assertEqual('1918-05-23', result[0]['start'])
        self.assertNotIn('tags', result[0]['options'])
        self.assertEqual('Crisp', result[0]['title'])
        
    def test_timemap_format_filters(self):
        result = self.tmapfilter.format(self.metadata)
        self.assertEqual('1918-05-23', result[0]['start'])
        self.assertEqual('[Assault]', result[0]['options']['tags'])
        self.assertEqual('Crisp', result[0]['title'])

    def test_get_filters(self):
        results = get_filters(self.filters)
        self.assertEqual(results[0]['name'],'victim_allegedcrime_brundage')
        self.assertEqual(results[0]['title'],'Alleged Crime')
        self.assertEqual(results[0]['prefix'],'ac_')
        self.assertEqual(results[0]['tags'][0][0],'Murder') 
        self.assertEqual(results[0]['tags'][0][1],'ac_murder') 
        self.assertEqual(results[0]['tags'][0][2],'127')
        
class GeoCoordinatesTest(TestCase):              
        
    def test_geo_properties(self):
        geo = GeoCoordinates(county="Macon")
        self.assertEqual(32.354068, geo.lat)
        self.assertEqual(-84.037633, geo.lon)
        
    def test_no_county_properties(self):
        try:
            geo = GeoCoordinates(county=None)
        except KeyError, err:
            self.assertRaises(KeyError)
            
    def test_bad_county_properties(self):
        try:
            geo = GeoCoordinates(county='Bogus')
        except KeyError, err:
            self.assertRaises(KeyError)            
