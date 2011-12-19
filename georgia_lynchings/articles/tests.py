import logging
import os

from django.test import TestCase, Client
from django.conf import settings
from django.core.management.base import CommandError
from django.core.urlresolvers import reverse
from georgia_lynchings.articles.models import NewspaperArticles


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
            
