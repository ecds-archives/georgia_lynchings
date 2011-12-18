import logging
import os

from django.test import TestCase, Client
from django.conf import settings
from django.core.urlresolvers import reverse

from georgia_lynchings.actors.models import Actor

class ActorTest(TestCase):

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
            
        
    def test_get_events_bogus_rowid(self):
        row_id = '0'
        title = 'No records found'
        # events_url = '/actors/0/macroevents/'        
        macroevents_url = reverse('macroevents', kwargs={'row_id': row_id})
        macroevents_response = self.client.get(macroevents_url)
        expected, got = 200, macroevents_response.status_code            
        self.assertEqual(row_id, macroevents_response.context['row_id'], 
            'Expected %s but returned %s for row_id' % (row_id, macroevents_response.context['row_id']))
        self.assertEqual(0, len(macroevents_response.context['resultSet']), 
            'Expected len 0 but returned %s for resultSet' % (len(macroevents_response.context['resultSet'])))
        self.assertEqual(title, macroevents_response.context['title'], 
            'Expected %s but returned %s for title' % (row_id, macroevents_response.context['title']))
            
    def test_events_url(self):
        row_id = '4569'
        title = 'negro (sam hose male )'
        # events_url = '/actors/4569/events/'        
        macroevents_url = reverse('macroevents', kwargs={'row_id': row_id})
        macroevents_response = self.client.get(macroevents_url)
        expected, got = 200, macroevents_response.status_code            
        self.assertEqual(row_id, macroevents_response.context['row_id'], 
            'Expected %s but returned %s for row_id' % (row_id, macroevents_response.context['row_id']))
        self.assertEqual(6, len(macroevents_response.context['resultSet']), 
            'Expected len 6 but returned %s for resultSet' % (len(macroevents_response.context['resultSet'])))
        self.assertEqual(title, macroevents_response.context['title'], 
            'Expected %s but returned %s for title' % (row_id, macroevents_response.context['title']))
 
