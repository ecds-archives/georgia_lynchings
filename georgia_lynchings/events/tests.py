from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from rdflib import Literal

from georgia_lynchings.events.models import MacroEvent

class MacroEventTest(TestCase):
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
        self.RANDOLPH_MACRO_ID = '208'        
        self.CAMPBELL_MACRO_ID = '360'
 
               

    def tearDown(self):
        # restore settings
        settings.SPARQL_STORE_API = self.sparql_store_api_orig
        settings.SPARQL_STORE_REPOSITORY = self.sparql_store_repo_orig 
            
    def test_basic_rdf_properties(self):
        # For now, just test that the MacroEvent class has a few basic
        # properties. These properties don't mean much quite yet, so as this
        # property-interpretation code is fleshed out these tests will
        # likely grow to test something more meaningful.
        self.assertTrue('setup_Complex.csv#r' in unicode(MacroEvent.rdf_type))
        self.assertTrue('data_Complex.csv#Identifier' in unicode(MacroEvent.label.prop))

        self.assertTrue('setup_xref_Complex-Complex.csv#r' in unicode(MacroEvent.events.prop))
        self.assertTrue('setup_Simplex.csv#r' in unicode(MacroEvent.county.prop))
        self.assertTrue('setup_Simplex.csv#r' in unicode(MacroEvent.victim.prop))
        self.assertTrue('setup_Simplex.csv#r' in unicode(MacroEvent.case_number.prop))
        self.assertTrue('setup_Simplex.csv#r' in unicode(MacroEvent.verified_semantic.prop))
        self.assertTrue('setup_Simplex.csv#r' in unicode(MacroEvent.verified_details.prop))
        self.assertTrue('setup_Simplex.csv#r' in unicode(MacroEvent.last_coded.prop))

    def test_get_victim(self):
        macro = MacroEvent(self.SAM_HOSE_MACRO_ID)
        self.assertEqual(macro.victim, 'Sam Hose')

        macro = MacroEvent(self.NONEXISTENT_MACRO_ID)
        self.assertEqual(macro.victim, None) 
        
    def test_get_cities(self):
        macro = MacroEvent(self.SAM_HOSE_MACRO_ID)
        expected, got = [u'palmetto'], macro.get_cities() 
        self.assertEqual(expected, got, 'Expected %s city list, got %s' % (expected, got))
        
        macro = MacroEvent(self.NONEXISTENT_MACRO_ID)
        expected, got = None, macro.get_cities() 
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
        
    def test_get_triplets(self):
        macro = MacroEvent(self.SAM_HOSE_MACRO_ID)
        eventdict = macro.get_triplets()       
        expected, got = 2, len(eventdict[u'lynching law creation (columbia)'] )
        self.assertEqual(expected, got, 'Expected %s triplet length, got %s' % (expected, got))
        expected, got = 8, len(eventdict[ u'seeking of a negro (palmetto)'] )
        self.assertEqual(expected, got, 'Expected %s triplet length, got %s' % (expected, got))
        expected, got = u'mob lynch', eventdict[u'seeking of a negro (palmetto)'][1][:9] 
        self.assertEqual(expected, got, 'Expected %s triplet length, got %s' % (expected, got))                    
                
        macro = MacroEvent(self.NONEXISTENT_MACRO_ID)
        expected, got = None, macro.get_triplets() 
        self.assertEqual(expected, got, 'Expected %s for nonexistant triplet macro id, got %s' % (expected, got)) 
                               
    def test_parto(self):
        macro = MacroEvent(self.RANDOLPH_MACRO_ID)
        resultSet = macro.get_participant_O()
        # Test macro event
        expected, got = 'Randolph', resultSet[7]['melabel']
        self.assertEqual(expected, got, 'Expected %s macro event, got %s' % (expected, got))        
        # Test name_of_indivd_actor
        expected, got = 'mother', resultSet[7]['name_of_indivd_actor']
        self.assertEqual(expected, got, 'Expected %s name_of_indivd_actor, got %s' % (expected, got))         
        # Test quantitative age
        expected, got = 'elderly', resultSet[7]['quantitative_age']
        self.assertEqual(expected, got, 'Expected %s quantitative_age, got %s' % (expected, got))
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
        resultSet = macro.get_participant_S()
        # Test macro event
        expected, got = 'Crisp', resultSet[7]['melabel']
        self.assertEqual(expected, got, 'Expected %s macro event, got %s' % (expected, got))        
        # Test name_of_indivd_actor
        expected, got = 'sheriff', resultSet[5]['name_of_indivd_actor']
        self.assertEqual(expected, got, 'Expected %s name_of_indivd_actor, got %s' % (expected, got))         
        # Test quantitative age
        expected, got = 'young', resultSet[7]['quantitative_age']
        self.assertEqual(expected, got, 'Expected %s quantitative_age, got %s' % (expected, got))
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
