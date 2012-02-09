import json
import logging
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from mock import patch, MagicMock
from rdflib import Literal
from pprint import pprint

from georgia_lynchings.events.models import MacroEvent, Event, SemanticTriplet, Victim
from georgia_lynchings.events.timemap import Timemap
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
        self.SAM_HOSE_MACRO_ID = '12'
        self.MERIWETHER_MACRO_ID = '25'        
        self.BROOKS_MACRO_ID = '57'        
        self.RANDOLPH_MACRO_ID = '208'        
        self.CAMPBELL_MACRO_ID = '360'

        self.EVENT_ID = '552'
        self.TRIPLET_ID = '555'
        self.VICTIM_ID = '135158'        

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
        self.assertEqual('Sam Hose', macro.victim)

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
        macro = MacroEvent(self.BROOKS_MACRO_ID)
        result = macro.get_details()
        # Test article total for BROOKS dcx:r57 macro event 
        expected, got = '3', result['articleTotal'] 
        self.assertEqual(expected, got, 'Expected %s articleTotal, got %s' % (expected, got))
        # Test event_type for BROOKS dcx:r57 macro event         
        expected, got = 'lynching', result['event_type'] 
        self.assertEqual(expected, got, 'Expected %s event_type, got %s' % (expected, got))
        # Test melabel for BROOKS dcx:r57 macro event 
        expected, got = 'Brooks', result['melabel'] 
        self.assertEqual(expected, got, 'Expected %s macro event label, got %s' % (expected, got))
        # Test evlabel for BROOKS dcx:r57 macro event 
        expected, got = 'lynching (senatobia)', result['events'][0]['evlabel'] 
        self.assertEqual(expected, got, 'Expected %s event label, got %s' % (expected, got))
        # Test location for BROOKS dcx:r57 macro event 
        expected, got = 'senatobia (city)', result['events'][0]['location'] 
        self.assertEqual(expected, got, 'Expected %s event label, got %s' % (expected, got))
        # Test mindate for BROOKS dcx:r57 macro event 
        expected, got = '1909-07-02', result['events'][0]['mindate'] 
        self.assertEqual(expected, got, 'Expected %s mindate, got %s' % (expected, got)) 
        # Test maxdate for BROOKS dcx:r57 macro event 
        expected, got = '1909-07-02', result['events'][0]['maxdate'] 
        self.assertEqual(expected, got, 'Expected %s maxdate, got %s' % (expected, got)) 
        # Test triplet_first for BROOKS dcx:r57 macro event 
        expected = 'mob hung (violence against people 7/2/1909 senatobia) negro (steven veasey male)'
        got = result['events'][0]['triplet_first'] 
        self.assertEqual(expected, got, 'Expected %s triplet_first, got %s' % (expected, got))

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
            
        macro = MacroEvent(self.MERIWETHER_MACRO_ID)
        result = macro.get_details()
        expected, got = 'murder', result['event_type'] 
        self.assertEqual(expected, got, 'Expected %s event_type, got %s' % (expected, got))         
        expected, got = 'reward of 250$; unknown lynchers', result['outcome'] 
        self.assertEqual(expected, got, 'Expected %s outcome, got %s' % (expected, got))
        expected, got = 'lynching; capture of the negro', result['reason'] 
        self.assertEqual(expected, got, 'Expected %s reason, got %s' % (expected, got))  
        expected, got = 'Meriwether', result['melabel'] 
        self.assertEqual(expected, got, 'Expected %s articleTotal, got %s' % (expected, got))                                            
                
        macro = MacroEvent(self.NONEXISTENT_MACRO_ID)
        expected, got = None, macro.get_details() 
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

        self.assertEqual(hose_data['victim'], 'Sam Hose')
        self.assertEqual(hose_data['min_date'], '1899-12-04')
        self.assertEqual(hose_data['max_date'], '1899-12-04')

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
        self.assertTrue(idata['complex_type'].endswith('#r52'))
        self.assertTrue(idata['label'].startswith('party (male unknown armed)'))
        self.assertTrue(idata['macro_event_uri'].endswith('#r1')) 
                
class ViewsTest(EventsAppTest):
    def test_get_articles_bogus_rowid(self):
        row_id = self.NONEXISTENT_MACRO_ID
        title = 'No records found'
        # articles_url = '/events/0/articles/'        
        articles_url = reverse('articles', kwargs={'row_id': row_id})
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
        articles_url = reverse('articles', kwargs={'row_id': row_id})
        articles_response = self.client.get(articles_url)
        expected, got = 200, articles_response.status_code
        self.assertEqual(expected, got, 'Expected %s status code, got %s' % (expected, got))
        self.assertEqual(row_id, articles_response.context['row_id'], 
            'Expected %s but returned %s for row_id' % (row_id, articles_response.context['row_id']))
        self.assertEqual(4, len(articles_response.context['resultSet']), 
            'Expected len 4 but returned %s for resultSet' % (len(articles_response.context['resultSet'])))
        self.assertEqual(title, articles_response.context['title'][:6], 
            'Expected %s but returned %s for title' % (row_id, articles_response.context['title'][:6]))
 
    def test_times_url(self):
        # times_url = '/events/times/'        
        times_url = reverse('times')       
        time_response = self.client.get(times_url)       
        
        expected, got = 200, time_response.status_code
        self.assertEqual(expected, got, 'Expected %s status code, got %s' % (expected, got))
        self.assertGreater(len(time_response.context['results']), 325, 
            'Expected len is greater than 325 but returned %s for results' % (len(time_response.context['results']))) 
          
        # test type of macro event label, should be literal
        self.assertTrue(isinstance(time_response.context['results'][0]['melabel'], Literal),
                        'Expected melabel type Literal')
        # test value of macro event label        
        expected, got = time_response.context['results'][0]['melabel'][:7], u'Houston'
        msg = 'Expected macro event label [%s] but returned [%s] for results' % (expected, got)
        self.assertEqual(expected, got, msg)
        
        # test value of mindate format        
        expected, got = time_response.context['results'][0]['mindate'], u'1879-11-25'
        msg = 'Expected mindate [%s] but returned [%s] for results' % (expected, got)
        self.assertEqual(expected, got, msg)
        msg = 'mindate pattern [%s] does not match yyyy-mm-dd' % (got)
        pattern = r'1\d\d\d-\d\d-\d\d'
        self.assertRegexpMatches(got, pattern, msg) 
        
        # test value of maxdate format        
        expected, got = time_response.context['results'][0]['maxdate'], u'1879-11-26'
        msg = 'Expected maxdate [%s] but returned [%s] for results' % (expected, got)
        self.assertEqual(expected, got, msg)
        msg = 'maxdate pattern [%s] does not match yyyy-mm-dd' % (got)
        pattern = r'1\d\d\d-\d\d-\d\d'
        self.assertRegexpMatches(got, pattern, msg)
        
    def test_macro_events_url(self):
        # times_url = '/events/'        
        macro_events_url = reverse('macro_events')       
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

        search_url = reverse('search')
        response = self.client.get(search_url, {'q': 'coweta'})

        self.assertContains(response, 'search results for')
        self.assertEqual(response.context['term'], 'coweta')
        self.assertEqual(response.context['results'], solr_result)
        self.assertTrue('form' in response.context)      

class TimemapTest(TestCase):
    def setUp(self):
        self.tmap = Timemap()   
        self.solr_items = [
            {'label': u'Debt Dispute', 
                'max_date': u'1896-06-02',
                'min_date': u'1896-06-01', 
                'row_id': u'89', 
                'victim_county_brundage': (u'Muscogee', u'Muscogee')},    
            {'label': u'Wild Talking',
                'max_date': u'1913-03-07',
                'min_date': u'1913-02-28',
                'row_id': u'240',
                'victim_county_brundage': (u'Habersham',)}
        ]
        
    def test_init(self):
        self.assertGreater(len(self.tmap.me_list), 300)
        
    def test_timemap_format(self):
        expected_result = [{'id': 'event',
                  'options': {'items': [{'end': '1896-06-02',
                                         'options': {'infoHtml': "<div><b>Debt Dispute</b></div><div>Start Date: 1896-06-01</div><div>Location: Muscogee County</div><div><a target='_blank' href='../89/details'>more info</a></div>"},
                                         'point': {'lat': 32.51071, 'lon': -84.874972},
                                         'start': '1896-06-01',
                                         'title': 'Debt Dispute'},
                                        {'end': '1913-03-07',
                                         'options': {'infoHtml': "<div><b>Wild Talking</b></div><div>Start Date: 1913-02-28</div><div>Location: Habersham County</div><div><a target='_blank' href='../240/details'>more info</a></div>"},
                                         'point': {'lat': 34.630446, 'lon': -83.529331},
                                         'start': '1913-02-28',
                                         'title': 'Wild Talking'}]},
                  'theme': 'red',
                  'title': 'Events',
                  'type': 'basic'}]

        result = self.tmap.timemap_format(self.solr_items)
        self.assertEqual(result, expected_result)  
        
    def test_create_timemap_item(self):
        expected_result = {'end': '1896-06-02',
                        'options': {'infoHtml': "<div><b>Debt Dispute</b></div><div>Start Date: 1896-06-01</div><div>Location: Muscogee County</div><div><a target='_blank' href='../89/details'>more info</a></div>"},
                        'point': {'lat': 32.51071, 'lon': -84.874972},
                        'start': '1896-06-01',
                        'title': 'Debt Dispute'}
        result = self.tmap.create_timemap_item(self.solr_items[0], 'Muscogee')
        self.assertEqual(result, expected_result)

    
