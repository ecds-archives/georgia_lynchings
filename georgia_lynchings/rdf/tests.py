import os
import StringIO

from django.conf import settings
from django.core.management.base import CommandError
from django.test import TestCase
from mock import patch
from rdflib import URIRef, Literal, Namespace, BNode, Variable, RDF, RDFS

from georgia_lynchings.rdf.sparql import SelectQuery
from georgia_lynchings.rdf.sparqlstore import SparqlStore, SparqlStoreException
from georgia_lynchings.rdf.management.commands import run_sparql_query
from georgia_lynchings.rdf.models import ComplexObject, RdfPropertyField, \
        ReversedRdfPropertyField, ChainedRdfPropertyField

class SparqlStoreTest(TestCase):
    def setUp(self):
        
        # override settings
        self.sparql_store_api_orig = settings.SPARQL_STORE_API
        settings.SPARQL_STORE_API = settings.TEST_SPARQL_STORE_API
        self.sparql_store_repo_orig = settings.SPARQL_STORE_REPOSITORY
        settings.SPARQL_STORE_REPOSITORY = settings.TEST_SPARQL_STORE_REPOSITORY          

        # Create a connection to the triplestore.
        self.sparqlstore=SparqlStore(url=settings.TEST_SPARQL_STORE_API, 
                                     repository=settings.TEST_SPARQL_STORE_REPOSITORY)

    def tearDown(self):
        # restore settings
        settings.SPARQL_STORE_API = self.sparql_store_api_orig
        settings.SPARQL_STORE_REPOSITORY = self.sparql_store_repo_orig
            
    def test_init(self):
        self.assertEqual(self.sparqlstore.url, settings.TEST_SPARQL_STORE_API)
        self.assertEqual(self.sparqlstore.repository, settings.TEST_SPARQL_STORE_REPOSITORY)
       
    def test_getResultType(self):
        self.assertEqual('application/sparql-results+xml', self.sparqlstore.getResultType('SPARQL_XML'))        
        self.assertEqual('application/sparql-results+json', self.sparqlstore.getResultType('SPARQL_JSON'))
        self.assertEqual('application/x-binary-rdf-results-table', self.sparqlstore.getResultType('BINARY_TABLE'))
        self.assertEqual('text/boolean', self.sparqlstore.getResultType('BOOLEAN'))
        
    def test_parse_xml_list_repositories(self):
        content_file = os.path.join(settings.BASE_DIR, 'rdf', 'fixtures', 'list_repositories.xml')
        content=open(content_file, 'rU').read()
        self.assertEqual(2568, len(content))        
        mapping=self.sparqlstore._parse_xml_results(content)
        self.assertEqual(4, len(mapping))
        self.assertIn('id', mapping[1])
        self.assertEqual('SYSTEM', mapping[0]['id'])
        
    def test_parse_xml_sparql_query(self):        
        content_file = os.path.join(settings.BASE_DIR, 'rdf', 'fixtures', 'articles_for_events.xml')
        content=open(content_file, 'rU').read()
        self.assertEqual(8428, len(content))        
        mapping=self.sparqlstore._parse_xml_results(content)
        self.assertEqual(12, len(mapping))
        self.assertIn('dd', mapping[1])
        self.assertIn('docpath', mapping[1]) 
        self.assertIn('event', mapping[1])
        self.assertIn('evlabel', mapping[1]) 
        self.assertIn('macro', mapping[1])
        self.assertIn('melabel', mapping[1])                        
        self.assertEqual(URIRef(u'http://galyn.example.com/source_data_files/data_Document.csv#r843'), mapping[3]['dd'])
        self.assertEqual(u'documents\\The Atlanta Constitution_04-21-1899_1.pdf', mapping[3]['docpath'])
        self.assertEqual(URIRef(u'http://galyn.example.com/source_data_files/data_Complex.csv#r3851'), mapping[3]['event']) 
        self.assertEqual(u'lynching (hawkinsville)', mapping[3]['evlabel'])
        self.assertEqual(URIRef(u'http://galyn.example.com/source_data_files/data_Complex.csv#r10'), mapping[3]['macro'])
        self.assertEqual(u'Pulaski (Curry Robertson)', mapping[3]['melabel'])

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
        self.sparqlstore=SparqlStore(url=settings.TEST_SPARQL_STORE_API, repository="abc")
        sparql_query_fixture = os.path.join(settings.BASE_DIR, 'rdf', 'fixtures', 'sparql_query.txt')
        sparqlquery=open(sparql_query_fixture, 'rU').read()                
        # Test that a SparqlStoreException is raised
        self.assertRaises(SparqlStoreException, self.sparqlstore.query, "SPARQL_XML", "POST", sparqlquery)  
        # Test for correct SparqlStoreException message
        try: self.sparqlstore.query("SPARQL_XML", "POST", open(sparql_query_fixture, 'rU').read())
        except SparqlStoreException as e: self.assertEqual('Unknown repository: abc', e.value) 

    # Test for triplestore site not responding
    def test_query_bad_url_exception(self):
        settings.SPARQL_STORE_API=None
        self.sparqlstore=SparqlStore(url='http://server.name.goes.here/openrdf-sesame/')
        # Test that an SparqlStoreException is raised                                  
        self.assertRaises(SparqlStoreException, self.sparqlstore.query, "SPARQL_XML", "GET") 
        # Test for correct SparqlStoreException message      
        try: self.sparqlstore.query("SPARQL_XML", "GET")
        except SparqlStoreException as e:
            self.assertEqual('Site is Down: http://server.name.goes.here', e.value[:42])             

class RunSparqlQueryCommandTest(TestCase):
    
    def setUp(self): 

        # override settings
        self.sparql_store_api_orig = settings.SPARQL_STORE_API
        settings.SPARQL_STORE_API = settings.TEST_SPARQL_STORE_API
        self.sparql_store_repo_orig = settings.SPARQL_STORE_REPOSITORY
        settings.SPARQL_STORE_REPOSITORY = settings.TEST_SPARQL_STORE_REPOSITORY      

        self.command = run_sparql_query.Command()
        # set mock stdout with stringio
        self.command.stdout = StringIO.StringIO()
            
    def tearDown(self):
        # restore settings
        settings.SPARQL_STORE_API = self.sparql_store_api_orig
        settings.SPARQL_STORE_REPOSITORY = self.sparql_store_repo_orig 
               
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
            {u'id': Literal('SYSTEM')},
            {u'id': Literal('galyn')},
            {u'id': Literal('galyn-2011-11-07')}, 
            {u'id': Literal('ben-test')}, 
            {u'id': Literal('galyn-test')},
        ]
        self.command.processResult(result=repo_result, list_repos=True)
        # check script output
        # output should equal:
        # "Repository List = [[u'SYSTEM', u'galyn', u'galyn-2011-11-07', u'ben-test', u'galyn-test']]"
        output = self.command.stdout.getvalue()    
        self.assert_('Repository List' in output)
        self.assert_('galyn' in output) 


class SelectQueryTest(TestCase):
    def test_bare_query(self):
        q = SelectQuery()
        self.assertEqual(unicode(q), 'SELECT * WHERE {  }')

    def test_append_tuple(self):
        q = SelectQuery()
        q.append((Variable('prop'), RDF.type, RDF.Property))
        q.append((Variable('prop'), RDFS.label, Literal('property')))
        expect_sparql = ('SELECT * WHERE { ' +
            '?prop ' +
                '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ' +
                '<http://www.w3.org/1999/02/22-rdf-syntax-ns#Property> . ' +
            '?prop ' +
                '<http://www.w3.org/2000/01/rdf-schema#label> ' +
                '"property" . ' +
            '}')
        self.assertEqual(unicode(q), expect_sparql)

    def test_variables(self):
        q = SelectQuery(results=['s', 'p', 'o'])
        q.append((Variable('s'), Variable('p'), Variable('o')))
        self.assertEqual(unicode(q), 'SELECT ?s ?p ?o WHERE { ?s ?p ?o . }')


class ComplexObjectTest(TestCase):
    sample = Namespace('http://example.com/#')

    def setUp(self):
        # create two ComplexObject subclasses in setUp() because if class
        # construction fails then we want the test to error. if this were
        # outside setUp, the whole module could fail to load in case of an
        # error.

        class SampleThingie(ComplexObject):
            # a ComplexObject without an rdf_type
            data = self.sample.data
            typed_data = RdfPropertyField(self.sample.typed_data,
                                          result_type=int)
        self.SampleThingie = SampleThingie
        self.thingie = SampleThingie(42)
        
        class SampleMutlipleThing(ComplexObject):
            # a ComplexObject without an rdf_type
            data = self.sample.data
            typed_data = RdfPropertyField(self.sample.typed_data,
                                          multiple=True)
        self.SampleMutlipleThing = SampleMutlipleThing
        self.thingies = SampleMutlipleThing(42)        

        class SampleWidget(ComplexObject):
            # a ComplexObject with an rdf_type
            rdf_type = self.sample.Widget
            value = self.sample.value
            rev_value = ReversedRdfPropertyField(value)
            chained_value = ChainedRdfPropertyField(value, value)
        self.SampleWidget = SampleWidget
        self.widget = SampleWidget(13)

    @patch('georgia_lynchings.rdf.models.SparqlStore')
    def test_sparql_generation_without_type_no_match(self, MockStore):
        mock_query = MockStore.return_value.query
        mock_query.return_value = []
        
        data = self.thingie.data

        self.assertEqual(mock_query.call_count, 1)
        args, kwargs = mock_query.call_args
        self.assertEqual(kwargs['sparql_query'],
            u'SELECT ?result WHERE { ?obj <http://example.com/#data> ?result . }')
        self.assertEqual(kwargs['initial_bindings'],
            {'obj': self.thingie.uri.n3()})
        self.assertEqual(data, None)

    @patch('georgia_lynchings.rdf.models.SparqlStore')
    def test_sparql_generation_without_type_with_match(self, MockStore):
        mock_query = MockStore.return_value.query
        mock_query.return_value = [{'result': Literal('stuff')}]
        
        data = self.thingie.data

        self.assertEqual(mock_query.call_count, 1)
        args, kwargs = mock_query.call_args
        self.assertEqual(kwargs['sparql_query'],
            u'SELECT ?result WHERE { ?obj <http://example.com/#data> ?result . }')
        self.assertEqual(kwargs['initial_bindings'],
            {'obj': self.thingie.uri.n3()})
        self.assertEqual(data, 'stuff')

    @patch('georgia_lynchings.rdf.models.SparqlStore')
    def test_sparql_generation_with_type_no_match(self, MockStore):
        mock_query = MockStore.return_value.query
        mock_query.return_value = []
        
        value = self.widget.value

        self.assertEqual(mock_query.call_count, 1)
        args, kwargs = mock_query.call_args
        self.assertEqual(kwargs['sparql_query'],
            u'SELECT ?result WHERE { ?obj <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.com/#Widget> . ?obj <http://example.com/#value> ?result . }')
        self.assertEqual(kwargs['initial_bindings'],
            {'obj': self.widget.uri.n3()})
        self.assertEqual(value, None)

    @patch('georgia_lynchings.rdf.models.SparqlStore')
    def test_sparql_generation_with_type_with_match(self, MockStore):
        mock_query = MockStore.return_value.query
        mock_query.return_value = [{'result': Literal('stuff')}]
        
        value = self.widget.value

        self.assertEqual(mock_query.call_count, 1)
        args, kwargs = mock_query.call_args
        self.assertEqual(kwargs['sparql_query'],
            u'SELECT ?result WHERE { ?obj <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.com/#Widget> . ?obj <http://example.com/#value> ?result . }')
        self.assertEqual(kwargs['initial_bindings'],
            {'obj': self.widget.uri.n3()})
        self.assertEqual(value, 'stuff')

    @patch('georgia_lynchings.rdf.models.SparqlStore')
    def test_reverse_sparql_generation(self, MockStore):
        mock_query = MockStore.return_value.query
        mock_query.return_value = []
        data = self.widget.rev_value

        self.assertEqual(mock_query.call_count, 1)
        args, kwargs = mock_query.call_args
        self.assertEqual(kwargs['sparql_query'],
            u'SELECT ?result WHERE { ?obj <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.com/#Widget> . ' + 
            u'?result <http://example.com/#value> ?obj . }')

    @patch('georgia_lynchings.rdf.models.SparqlStore')
    @patch('georgia_lynchings.rdf.models.BNode')
    def test_chained_sparql_generation(self, MockBNode, MockStore):
        mock_query = MockStore.return_value.query
        mock_query.return_value = []
        MockBNode.return_value = BNode('FAKEID')

        data = self.widget.chained_value

        self.maxDiff = None
        self.assertEqual(mock_query.call_count, 1)
        args, kwargs = mock_query.call_args
        self.assertEqual(kwargs['sparql_query'],
            u'SELECT ?result WHERE { ?obj <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.com/#Widget> . ' + 
            u'?obj <http://example.com/#value> _:FAKEID . ' +
            u'_:FAKEID <http://example.com/#value> ?result . ' +
            u'}')

    @patch('georgia_lynchings.rdf.models.SparqlStore')
    def test_typed_property(self, MockStore):
        mock_query = MockStore.return_value.query
        mock_query.return_value = [{'result': '14'}]
        
        typed_data = self.thingie.typed_data
        self.assertEqual(typed_data, 14)
        
    @patch('georgia_lynchings.rdf.models.SparqlStore')
    def test_property_multiple_results(self, MockStore):
        mock_query = MockStore.return_value.query
        mock_query.return_value = [{'result': ['14']},{'result': ['41']}]       
        typed_data = self.thingies.typed_data
        self.assertIn('14', typed_data[0])        
