import os
import StringIO

from django.conf import settings
from django.core.management.base import CommandError
from django.test import TestCase
from mock import patch
from rdflib import URIRef, Literal, Namespace, BNode, Variable, RDF, RDFS
import rdflib

from georgia_lynchings.rdf.ns import ix_mbd, scxn, sxcxcxn
from georgia_lynchings.rdf.sparql import SelectQuery
from georgia_lynchings.rdf.sparqlstore import SparqlStore, SparqlStoreException
from georgia_lynchings.rdf.fields import RdfPropertyField, \
        ReversedRdfPropertyField, ChainedRdfPropertyField
from georgia_lynchings.rdf.models import ComplexObject

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
       
    def test_missing_sparql_store_api(self):
        settings.SPARQL_STORE_API = None        
        # Test that a SparqlStoreException is raised
        self.assertRaises(SparqlStoreException, SparqlStore)

    def test_missing_sparql_store_repository(self):
        settings.SPARQL_STORE_REPOSITORY = None        
        # Test that a SparqlStoreException is raised
        self.assertRaises(SparqlStoreException, SparqlStore)
               
    # Test raised exception for unknown repository                     
    def test_query_unknown_repository(self):
        self.sparqlstore=SparqlStore(url=settings.TEST_SPARQL_STORE_API, repository="abc")
        sparqlquery = 'SELECT * WHERE { ?s ?p ?o }'
        # Test that a SparqlStoreException is raised
        self.assertRaises(SparqlStoreException, self.sparqlstore.query, sparqlquery)  

    # Test for triplestore site not responding
    def test_query_bad_url_exception(self):
        settings.SPARQL_STORE_API=None
        self.sparqlstore=SparqlStore(url='http://server.name.goes.here/openrdf-sesame/')
        sparqlquery = 'SELECT * WHERE { ?s ?p ?o }'
        # Test that an SparqlStoreException is raised                                  
        self.assertRaises(SparqlStoreException, self.sparqlstore.query, sparqlquery) 


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
        
    def test_optional_pattern(self):
        q = SelectQuery(results=['s', 'p', 'o'])
        q.append((Variable('s'), Variable('p'), Variable('o')))        
        q.append((Variable('a'), Variable('b'), Variable('c')), optional=True)
        self.assertEqual(unicode(q), 'SELECT ?s ?p ?o WHERE { ?s ?p ?o . OPTIONAL { ?a ?b ?c . } }')

    def test_distinct_query(self):
        q = SelectQuery(results=['s', 'p', 'o'], distinct=True)
        q.append((Variable('s'), Variable('p'), Variable('o')))        
        self.assertEqual(unicode(q), 'SELECT DISTINCT ?s ?p ?o WHERE { ?s ?p ?o . }')

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
        
        class SampleMultipleThing(ComplexObject):
            # a ComplexObject without an rdf_type
            data = self.sample.data
            typed_data = RdfPropertyField(self.sample.typed_data,
                                          multiple=True)
        self.SampleMultipleThing = SampleMultipleThing
        self.thingies = SampleMultipleThing(42)        

        class SampleWidget(ComplexObject):
            # a ComplexObject with an rdf_type
            rdf_type = self.sample.Widget
            value = self.sample.value
            rev_value = ReversedRdfPropertyField(value)
            chained_value = ChainedRdfPropertyField(value, value)
        self.SampleWidget = SampleWidget
        self.widget = SampleWidget(13)

    @patch('georgia_lynchings.rdf.fields.SparqlStore')
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

    @patch('georgia_lynchings.rdf.fields.SparqlStore')
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

    @patch('georgia_lynchings.rdf.fields.SparqlStore')
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

    @patch('georgia_lynchings.rdf.fields.SparqlStore')
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

    @patch('georgia_lynchings.rdf.fields.SparqlStore')
    def test_reverse_sparql_generation(self, MockStore):
        mock_query = MockStore.return_value.query
        mock_query.return_value = []
        data = self.widget.rev_value

        self.assertEqual(mock_query.call_count, 1)
        args, kwargs = mock_query.call_args
        self.assertEqual(kwargs['sparql_query'],
            u'SELECT ?result WHERE { ?obj <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.com/#Widget> . ' + 
            u'?result <http://example.com/#value> ?obj . }')

    @patch('georgia_lynchings.rdf.fields.SparqlStore')
    @patch('uuid.uuid4')
    def test_chained_sparql_generation(self, mockuuid4, MockStore):
        mock_query = MockStore.return_value.query
        mock_query.return_value = []
        mockuuid4.return_value = 'FAKEID'

        data = self.widget.chained_value

        self.maxDiff = None
        self.assertEqual(mock_query.call_count, 1)
        args, kwargs = mock_query.call_args
        self.assertEqual(kwargs['sparql_query'],
            u'SELECT ?result WHERE { ?obj <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.com/#Widget> . ' + 
            u'?obj <http://example.com/#value> ?_FAKEID . ' +
            u'?_FAKEID <http://example.com/#value> ?result . ' +
            u'}')

    @patch('georgia_lynchings.rdf.fields.SparqlStore')
    def test_typed_property(self, MockStore):
        mock_query = MockStore.return_value.query
        mock_query.return_value = [{'result': '14'}]
        
        typed_data = self.thingie.typed_data
        self.assertEqual(typed_data, 14)
        
    @patch('georgia_lynchings.rdf.fields.SparqlStore')
    def test_property_multiple_results(self, MockStore):
        mock_query = MockStore.return_value.query
        mock_query.return_value = [{'result': ['14']},{'result': ['41']}]       
        typed_data = self.thingies.typed_data
        self.assertIn('14', typed_data[0]) 
        

class QuerySetTest(TestCase):
    sample = Namespace('http://example.com/#')

    def setUp(self):
        # create ComplexObject subclasses in setUp() because if class
        # construction fails then we want the test to error. if this were
        # outside setUp, the whole module could fail to load in case of an
        # error.

        class SampleWidget(ComplexObject):
            rdf_type = self.sample.Widget
            example_val = self.sample.val
        self.SampleWidget = SampleWidget
        self.widget = SampleWidget(13)

        class SampleThingie(ComplexObject):
            rdf_type = self.sample.Thingie
            widgets = RdfPropertyField(self.sample.has_widget,
                                       result_type=SampleWidget,
                                       multiple=True)
        self.SampleThingie = SampleThingie
        self.thingie = SampleThingie(42)

    def test_all_objects_query(self):
        qs = self.SampleThingie.objects.all()
        self.assertEqual(unicode(qs.queries[0]), 'SELECT ?result WHERE { ' +
                                                   '?result <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.com/#Thingie> . ' +
                                                 '}')

    def test_unbound_subobjects_query(self):
        qs = self.SampleThingie.objects.widgets.all()
        self.assertEqual(unicode(qs.queries[0]), 'SELECT ?result WHERE { ' +
                                                   '?obj <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.com/#Thingie> . ' +
                                                   '?obj <http://example.com/#has_widget> ?result . ' +
                                                 '}')

    def test_fields_query(self):
        qs = self.thingie.objects.widgets.fields('example_val')
        self.assertEqual(unicode(qs.queries[0]), 'SELECT ?result ?example_val WHERE { ' +
                                                   '?obj <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.com/#Thingie> . ' +
                                                   '?obj <http://example.com/#has_widget> ?result . ' +
                                                   'OPTIONAL { ' +
                                                     '?result <http://example.com/#val> ?example_val . ' +
                                                   '} ' +
                                                 '}')

class NsTest(TestCase):
    def test_constructed_stmts_ns(self):
        expected = rdflib.term.URIRef('http://galyn.example.com/constructed_statements/index/macros_by_date/#mindate')
        self.assertEqual(ix_mbd.mindate, expected)

    def test_source_file_ns(self):
        expected = rdflib.term.URIRef('http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name-Event')
        self.assertEqual(sxcxcxn.Event, expected)
        expected = rdflib.term.URIRef('http://galyn.example.com/source_data_files/setup_Complex.csv#name-Macro_Event')
        self.assertEqual(scxn.Macro_Event, expected)
