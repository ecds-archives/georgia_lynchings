import logging
import os

from django.test import TestCase
from django.conf import settings
from django.core.management.base import CommandError

from georgia_lynchings.events.abstractquery import AbstractQuery, Variable, AbstractQueryException
from georgia_lynchings.events.models import MacroEvent
from georgia_lynchings.events.sparqlstore import SparqlStore, SparqlStoreException
from georgia_lynchings.events.management.commands import run_sparql_query
import httplib2
import StringIO

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

class AbstractQueryTest(TestCase):                           
            
    def test_VariableClass(self):       
        result=Variable(value='macro')    
        self.assertEqual('?macro', result.value)

    def test_setDistinct(self):
        self.abstractquery=AbstractQuery()  
        self.assertEqual(True, self.abstractquery.setDistinct(True))
        self.assertEqual(False, self.abstractquery.setDistinct(False))         
        self.assertEqual(False, self.abstractquery.setDistinct())        
        # Test that a AbstractQueryException is raised                
        self.assertRaises(AbstractQueryException, self.abstractquery.setDistinct, "distinctblah1") 
        # Test for correct AbstractQueryException message
        try: self.abstractquery.setDistinct('distinctblah2')
        except AbstractQueryException as e:
            self.assertEqual('Invalid value for distinct: distinctblah2', e.value) 
           
    def test_setReduced(self):
        self.abstractquery=AbstractQuery()  
        self.assertEqual(True, self.abstractquery.setReduced(True))
        self.assertEqual(False, self.abstractquery.setReduced(False))        
        self.assertEqual(False, self.abstractquery.setReduced())        
        # Test that a AbstractQueryException is raised                
        self.assertRaises(AbstractQueryException, self.abstractquery.setDistinct, "reducedblah1") 
        # Test for correct AbstractQueryException message
        try: self.abstractquery.setReduced('reducedblah2')
        except AbstractQueryException as e:
            self.assertEqual('Invalid value for reduced: reducedblah2', e.value)
            
    def test_setLimit(self):
        self.abstractquery=AbstractQuery()  
        self.assertEqual(None, self.abstractquery.setLimit(None))
        self.assertEqual(None, self.abstractquery.setLimit(0))
        self.assertEqual(5, self.abstractquery.setLimit(5))
        # Test that a AbstractQueryException is raised                
        self.assertRaises(AbstractQueryException, self.abstractquery.setLimit, "limitone") 
        # Test for correct AbstractQueryException message
        try: self.assertEqual(None, self.abstractquery.setLimit('limittwo'))
        except AbstractQueryException as e:
            self.assertEqual('LIMIT value must be an integer: limittwo', e.value)

    def test_setOffset(self):
        self.abstractquery=AbstractQuery()  
        self.assertEqual(None, self.abstractquery.setOffset(None))
        self.assertEqual(None, self.abstractquery.setOffset(0))
        self.assertEqual(6, self.abstractquery.setOffset(6))
        # Test that a AbstractQueryException is raised                
        self.assertRaises(AbstractQueryException, self.abstractquery.setOffset, "offsetone") 
        # Test for correct AbstractQueryException message
        try: self.assertEqual(None, self.abstractquery.setOffset('offsettwo'))
        except AbstractQueryException as e:
            self.assertEqual('OFFSET value must be an integer: offsettwo', e.value)
            
    def test_setOrderBy(self):
        self.abstractquery=AbstractQuery()  
        self.assertEqual(None, self.abstractquery.setOrderBy(None))
        self.assertEqual('person', self.abstractquery.setOrderBy('person'))       
        # Test that a AbstractQueryException is raised                
        self.assertRaises(AbstractQueryException, self.abstractquery.setOrderBy, 6) 
        # Test for correct AbstractQueryException message
        try: self.assertEqual(None, self.abstractquery.setOrderBy(7))
        except AbstractQueryException as e:
            self.assertEqual('ORDER BY value must be a string: 7', e.value)
            
    def test_setGroupBy(self):
        self.abstractquery=AbstractQuery()  
        self.assertEqual(None, self.abstractquery.setGroupBy(None))
        self.assertEqual('place', self.abstractquery.setGroupBy('place'))       
        # Test that a AbstractQueryException is raised                
        self.assertRaises(AbstractQueryException, self.abstractquery.setGroupBy, 8) 
        # Test for correct AbstractQueryException message
        try: self.assertEqual(None, self.abstractquery.setGroupBy(9))
        except AbstractQueryException as e:
            self.assertEqual('GROUP BY value must be a string: 9', e.value) 
            
    def test_setHaving(self):
        self.abstractquery=AbstractQuery()  
        self.assertEqual(None, self.abstractquery.setHaving(None))
        self.assertEqual('place', self.abstractquery.setHaving('place'))       
        # Test that a AbstractQueryException is raised                
        self.assertRaises(AbstractQueryException, self.abstractquery.setHaving, 8) 
        # Test for correct AbstractQueryException message
        try: self.assertEqual(None, self.abstractquery.setHaving(9))
        except AbstractQueryException as e:
            self.assertEqual('HAVING value must be a string: 9', e.value)                                               

class SparqlStoreTest(TestCase):
    def setUp(self):
        # set the triplestore properties for testing.
        settings.SPARQL_STORE_API = 'http://wilson.library.emory.edu:8180/openrdf-sesame/'  
        settings.SPARQL_STORE_REPOSITORY = 'galyn-test'
                
        # Create a connection to the triplestore.
        self.sparqlstore=SparqlStore(url=settings.SPARQL_STORE_API, 
                                     repository=settings.SPARQL_STORE_REPOSITORY)                                    
            
    def test_init(self):
        self.assertEqual(self.sparqlstore.url, settings.SPARQL_STORE_API)
        self.assertEqual(self.sparqlstore.repository, settings.SPARQL_STORE_REPOSITORY)
        
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

    def test_missing_sparql_store_api(self):
        settings.SPARQL_STORE_API = None        
        # Test that a SparqlStoreException is raised
        self.assertRaises(SparqlStoreException, SparqlStore)
        # Test for correct SparqlStoreException message
        try: self.sparqlstore=SparqlStore()
        except SparqlStoreException as e:  
           self.assertEqual('SPARQL_STORE_API must be configured in localsettings.py', e.value)        

    def test_missing_sparql_store_repository(self):
        settings.SPARQL_STORE_REPOSITORY = None        
        # Test that a SparqlStoreException is raised
        self.assertRaises(SparqlStoreException, SparqlStore)
        # Test for correct SparqlStoreException message
        try: self.sparqlstore=SparqlStore()
        except SparqlStoreException as e:  
           self.assertEqual('SPARQL_STORE_REPOSITORY must be configured in localsettings.py', e.value)  
                
    # Test raised exception for unknown repository                     
    def test_query_unknown_repository(self):
        self.sparqlstore=SparqlStore(url=settings.SPARQL_STORE_API, repository="abc")
        sparql_query_fixture = os.path.join(settings.BASE_DIR, 'events', 'fixtures', 'sparql_query.txt')
        sparqlquery=open(sparql_query_fixture, 'rU').read()                
        # Test that a SparqlStoreException is raised
        self.assertRaises(SparqlStoreException, self.sparqlstore.query, "SPARQL_XML", "POST", sparqlquery)  
        # Test for correct SparqlStoreException message
        try: self.sparqlstore.query("SPARQL_XML", "POST", open(sparql_query_fixture, 'rU').read())
        except SparqlStoreException as e: self.assertEqual('Unknown repository: abc', e.value) 

    # Test for triplestore site not responding
    def test_query_bad_url_exception(self):
        self.sparqlstore=SparqlStore(url='http://server.name.goes.here/openrdf-sesame/')        
        # Test that an SparqlStoreException is raised                                  
        self.assertRaises(SparqlStoreException, self.sparqlstore.query, "SPARQL_XML", "GET")         
        # Test for correct SparqlStoreException message      
        try: self.sparqlstore.query("SPARQL_XML", "GET")
        except SparqlStoreException as e:
            self.assertEqual('Site is Down: http://server.name.goes.here', e.value[:42])               

    # Test to show sesame bug on sparql query with "GROUP BY"
    # Note: this sparql query work in the GUI but not via the API
    def test_sesame_GROUP_BY_bug_malformed_query(self):
        sparql_query_fixture = os.path.join(settings.BASE_DIR, 'events', 'fixtures', 'sparql_query_fail.txt')
        sparqlquery=open(sparql_query_fixture, 'rU').read()
        # Test that an SparqlStoreException is raised
        self.assertRaises(SparqlStoreException, self.sparqlstore.query, "SPARQL_XML", "POST", sparqlquery)
        # Test for correct SparqlStoreException message 
        try: result = self.sparqlstore.query("SPARQL_XML", "POST", sparqlquery)
        except SparqlStoreException as e: self.assertEqual('MALFORMED QUERY: Encountered', e.value[:28])              

class RunSparqlQueryCommandTest(TestCase):
    
    def setUp(self):
        # set the triplestore properties for testing.
        settings.SPARQL_STORE_API = 'http://wilson.library.emory.edu:8180/openrdf-sesame/'  
        settings.SPARQL_STORE_REPOSITORY = 'galyn-test'
              
        self.command = run_sparql_query.Command()
        # set mock stdout with stringio
        self.command.stdout = StringIO.StringIO()
            
    def tearDown(self):
        self.command.stdout.close()
        
    def test_missing_sparql_store_api(self):
        settings.SPARQL_STORE_API = None
        self.assertRaises(CommandError, self.command.handle)

    def test_missing_sparql_store_repository(self):
        settings.SPARQL_STORE_REPOSITORY = None
        self.assertRaises(CommandError, self.command.handle)
       
    # Test for triplestore site not responding
    def test_list_repos(self):
        repo_result=[
        {u'id': {'type': 'literal', 'value': u'SYSTEM'}}, 
        {u'id': {'type': 'literal', 'value': u'galyn'}}, 
        {u'id': {'type': 'literal', 'value': u'galyn-2011-11-07'}}, 
        {u'id': {'type': 'literal', 'value': u'ben-test'}}, 
        {u'id': {'type': 'literal', 'value': u'galyn-test'}}]
        self.command.processResult(result=repo_result, list_repos=True)
        # check script output
        # output should equal:
        # "Repository List = [[u'SYSTEM', u'galyn', u'galyn-2011-11-07', u'ben-test', u'galyn-test']]"
        output = self.command.stdout.getvalue()    
        self.assert_('Repository List' in output)
        self.assert_('galyn' in output) 
               
    # Test for triplestore site not responding
    def test_ppdict(self):
        repo_result=[
        {u'id': {'type': 'literal', 'value': u'SYSTEM'}}, 
        {u'id': {'type': 'literal', 'value': u'galyn'}}, 
        {u'id': {'type': 'literal', 'value': u'galyn-2011-11-07'}}, 
        {u'id': {'type': 'literal', 'value': u'ben-test'}}, 
        {u'id': {'type': 'literal', 'value': u'galyn-test'}}]
        self.command.processResult(result=repo_result, ppdict=True)
        # check script output
        # "Repository List = [[u'SYSTEM', u'galyn', u'galyn-2011-11-07', u'ben-test', u'galyn-test']]"
        output = self.command.stdout.getvalue()
        self.assert_('PrettyPrint' in output)        
