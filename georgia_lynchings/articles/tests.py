from django.test import TestCase, Client
from django.conf import settings
from django.core.urlresolvers import reverse
from rdflib import Literal

from georgia_lynchings.articles.models import all_articles


class NewspaperArticlesTest(TestCase):

    def setUp(self):
        self.client = Client()  
        # override settings
        self.sparql_store_api_orig = settings.SPARQL_STORE_API
        settings.SPARQL_STORE_API = settings.TEST_SPARQL_STORE_API
        self.sparql_store_repo_orig = settings.SPARQL_STORE_REPOSITORY
        settings.SPARQL_STORE_REPOSITORY = settings.TEST_SPARQL_STORE_REPOSITORY      
            
    def tearDown(self):
        # restore settings
        settings.SPARQL_STORE_API = self.sparql_store_api_orig
        settings.SPARQL_STORE_REPOSITORY = self.sparql_store_repo_orig
       
    def test_articles_url(self):       
        articles_url = reverse('articles:newspaper_articles')       
        articles_response = self.client.get(articles_url)

        expected, got = 200, articles_response.status_code
        self.assertEqual(expected, got, 'Expected %s status code, got %s' % (expected, got))
        self.assertGreater(len(articles_response.context['resultSet']), 325, 
            'Expected len is greater than 325 but returned %s for resultSet' % (len(articles_response.context['resultSet']))) 
          
        # docpath would normally be a Literal, but it's currently being
        # manually patched in # georgia_lynchings.articles.models.all_articles,
        # making it a unicode.
        self.assertTrue(isinstance(articles_response.context['resultSet'][0]['docpath'], unicode),
                        'Expected docpath type unicode (got %s)' % (articles_response.context['resultSet'][0]['docpath'].__class__.__name__,))
        # test value of docpath        
        expected, got = str(articles_response.context['resultSet'][0]['docpath']), 'The Atlanta Daily Constitution_11-26-1879_1.pdf'
        msg = 'Expected docpath [%s] but returned [%s] for resultSet' % (expected, got)
        self.assertEqual(expected, got, msg)
        
        # test value of docpath_link        
        expected, got = articles_response.context['resultSet'][0]['docpath_link'][:9], u'documents'
        msg = 'Expected docpath_link [%s] but returned [%s] for resultSet' % (expected, got)
        self.assertEqual(expected, got, msg)
        
        # test type of papername, should be literal
        self.assertTrue(isinstance(articles_response.context['resultSet'][0]['papername'], Literal),
                        'Expected papername type Literal')
        self.assertEqual(expected, got, msg)
        # test value of papername        
        expected, got = str(articles_response.context['resultSet'][0]['papername']), 'The Atlanta Daily Constitution'
        msg = 'Expected papername [%s] but returned [%s] for resultSet' % (expected, got)
        self.assertEqual(expected, got, msg) 
        
        # test type of articlepage, should be literal
        self.assertTrue(isinstance(articles_response.context['resultSet'][0]['articlepage'], Literal),
                        'Expected articlepage type Literal')
        self.assertEqual(expected, got, msg)
        # test value of articlepage        
        expected, got = articles_response.context['resultSet'][0]['articlepage'], u'1'
        msg = 'Expected articlepage [%s] but returned [%s] for resultSet' % (expected, got)
        self.assertEqual(expected, got, msg) 
        
        # test type of paperdate, should be literal
        self.assertTrue(isinstance(articles_response.context['resultSet'][0]['paperdate'], Literal),
                        'Expected paperdate type Literal')
        self.assertEqual(expected, got, msg)
        # test value of paperdate        
        expected, got = str(articles_response.context['resultSet'][0]['paperdate']), u'1879-11-26'
        msg = 'Expected paperdate [%s] but returned [%s] for resultSet' % (expected, got)
        self.assertEqual(expected, got, msg)     
