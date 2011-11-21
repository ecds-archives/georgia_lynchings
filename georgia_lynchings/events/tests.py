import logging
import os

from django.test import TestCase
from django.conf import settings

from georgia_lynchings.events.models import MacroEvent
from georgia_lynchings.events.sparqlstore import SparqlStore, SparqlStoreException
import httplib2

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
        

class SparqlStoreTest(TestCase):
    def setUp(self):
        # Create a connection to the triplestore.
        self.sparqlstore=SparqlStore(url=settings.SPARQL_STORE_API_TEST, 
                                     repository=settings.SPARQL_STORE_REPOSITORY_TEST)                                    
            
    def test_init(self):
        self.assertEqual(self.sparqlstore.url, settings.SPARQL_STORE_API_TEST)
        self.assertEqual(self.sparqlstore.repository, settings.SPARQL_STORE_REPOSITORY_TEST)
        
    def test_getResultType(self):
        self.assertEqual('application/sparql-results+xml', self.sparqlstore.getResultType('SPARQL_XML'))        
        self.assertEqual('application/sparql-results+json', self.sparqlstore.getResultType('SPARQL_JSON'))
        self.assertEqual('application/x-binary-rdf-results-table', self.sparqlstore.getResultType('BINARY_TABLE'))
        self.assertEqual('text/boolean', self.sparqlstore.getResultType('BOOLEAN'))
        
    def test_Xml2Dict_list_repositories(self):
        content_file = os.path.join(settings.BASE_DIR, 'events', 'fixtures', 'list_repositories.xml')
        content=open(content_file, 'rU').read()
        self.assertEqual(2568, len(content))        
        mapping=self.sparqlstore.Xml2Dict(content)
        self.assertEqual(4, len(mapping))
        self.assertIn('id', mapping[1].keys())
        self.assertEqual('SYSTEM', mapping[0]['id']['value'])
        
    def test_Xml2Dict_sparql_query(self):        
        content_file = os.path.join(settings.BASE_DIR, 'events', 'fixtures', 'articles_for_events.xml')
        content=open(content_file, 'rU').read()
        self.assertEqual(8428, len(content))        
        mapping=self.sparqlstore.Xml2Dict(content)
        self.assertEqual(12, len(mapping))
        self.assertIn('dd', mapping[1].keys())
        self.assertIn('docpath', mapping[1].keys()) 
        self.assertIn('event', mapping[1].keys())
        self.assertIn('evlabel', mapping[1].keys()) 
        self.assertIn('macro', mapping[1].keys())
        self.assertIn('melabel', mapping[1].keys())                        
        self.assertEqual(u'http://galyn.example.com/source_data_files/data_Document.csv#r843', mapping[3]['dd']['value'])
        self.assertEqual(u'documents\\The Atlanta Constitution_04-21-1899_1.pdf', mapping[3]['docpath']['value'])
        self.assertEqual(u'http://galyn.example.com/source_data_files/data_Complex.csv#r3851', mapping[3]['event']['value']) 
        self.assertEqual(u'lynching (hawkinsville)', mapping[3]['evlabel']['value'])                 
        self.assertEqual(u'http://galyn.example.com/source_data_files/data_Complex.csv#r10', mapping[3]['macro']['value'])          
        self.assertEqual(u'Pulaski (Curry Robertson)', mapping[3]['melabel']['value'])

    def test_query_unknown_repository_exception(self):
        try:
            self.sparqlstore=SparqlStore(url=settings.SPARQL_STORE_API_TEST, repository="abc")
            sparql_query_fixture = os.path.join(settings.BASE_DIR, 'events', 'fixtures', 'sparql_query.txt')                                   
            self.sparqlstore.query("SPARQL_XML", "POST", open(sparql_query_fixture, 'rU').read())
        except SparqlStoreException as e:  
           self.assertEqual('Unknown repository: abc', e.value)
           
    def test_query_unknown_repository(self):
        self.sparqlstore=SparqlStore(url=settings.SPARQL_STORE_API_TEST, repository="abc")
        sparql_query_fixture = os.path.join(settings.BASE_DIR, 'events', 'fixtures', 'sparql_query.txt')
        sparqlquery=open(sparql_query_fixture, 'rU').read()                                     
        self.assertRaises(Exception, self.sparqlstore.query, ["SPARQL_XML", "POST", sparqlquery])       
        
    def test_query_bad_url_exception(self):
        try:
            self.sparqlstore=SparqlStore(url='http://server.name.goes.here/openrdf-sesame/',
                                     repository=settings.SPARQL_STORE_REPOSITORY_TEST)                                  
            self.sparqlstore.query("SPARQL_XML", "GET")
        except SparqlStoreException as e:
            self.assertEqual('Site is Down: http://server.name.goes.here/openrdf-sesame/', e.value)               
