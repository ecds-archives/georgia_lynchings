from django.test import TestCase, Client
from django.conf import settings
from django.core.urlresolvers import reverse

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
        self.SAM_HOSE_MACRO_ID = '12'

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
        
    def test_get_articles_bogus_rowid(self):
        row_id = self.NONEXISTENT_MACRO_ID
        title = 'No records found'
        # articles_url = '/events/0/articles/'        
        articles_url = reverse('articles', kwargs={'row_id': row_id})
        articles_response = self.client.get(articles_url)
        expected, got = 200, articles_response.status_code            
        self.assertEqual(row_id, articles_response.context['row_id'], 
            'Expected %s but returned %s for row_id' % (row_id, articles_response.context['row_id']))
        self.assertEqual(0, len(articles_response.context['resultSet']), 
            'Expected len 0 but returned %s for resultSet' % (len(articles_response.context['resultSet'])))
        self.assertEqual(title, articles_response.context['title'], 
            'Expected %s but returned %s for title' % (row_id, articles_response.context['title']))

    def test_articles_url(self):
        row_id = self.SAM_HOSE_MACRO_ID
        title = 'Coweta (Sam Hose)'
        # articles_url = '/events/12/articles/'        
        articles_url = reverse('articles', kwargs={'row_id': row_id})
        articles_response = self.client.get(articles_url)
        expected, got = 200, articles_response.status_code            
        self.assertEqual(row_id, articles_response.context['row_id'], 
            'Expected %s but returned %s for row_id' % (row_id, articles_response.context['row_id']))
        self.assertEqual(4, len(articles_response.context['resultSet']), 
            'Expected len 4 but returned %s for resultSet' % (len(articles_response.context['resultSet'])))
        self.assertEqual(title, articles_response.context['title'], 
            'Expected %s but returned %s for title' % (row_id, articles_response.context['title']))
 
    def test_times_url(self):
        # times_url = '/events/times/'        
        times_url = reverse('times')       
        time_response = self.client.get(times_url)       
        
        expected, got = 200, time_response.status_code
        self.assertEqual(expected, got, 'Expected %s status code, got %s' % (expected, got))
        self.assertEqual(345, len(time_response.context['results']), 
            'Expected len 345 but returned %s for results' % (len(time_response.context['results']))) 
          
        # test type of macro event label, should be literal
        expected, got = time_response.context['results'][0]['melabel']['type'], "literal"
        msg = 'Expected macro event label type [%s] but returned [%s] for results' % (expected, got)
        self.assertEqual(expected, got, msg)
        # test value of macro event label        
        expected, got = time_response.context['results'][0]['melabel']['value'], u'Houston (Henry Walker)'
        msg = 'Expected macro event label [%s] but returned [%s] for results' % (expected, got)
        self.assertEqual(expected, got, msg)
        
        # test value of mindate format        
        expected, got = time_response.context['results'][0]['mindate']['value'], u'1879-11-25'
        msg = 'Expected mindate [%s] but returned [%s] for results' % (expected, got)
        self.assertEqual(expected, got, msg)
        msg = 'mindate pattern [%s] does not match yyyy-mm-dd' % (got)
        pattern = r'1\d\d\d-\d\d-\d\d'
        self.assertRegexpMatches(got, pattern, msg) 
        
        # test value of maxdate format        
        expected, got = time_response.context['results'][0]['maxdate']['value'], u'1879-11-26'
        msg = 'Expected maxdate [%s] but returned [%s] for results' % (expected, got)
        self.assertEqual(expected, got, msg)
        msg = 'maxdate pattern [%s] does not match yyyy-mm-dd' % (got)
        pattern = r'1\d\d\d-\d\d-\d\d'
        self.assertRegexpMatches(got, pattern, msg)
