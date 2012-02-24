from rdflib import Variable, RDF
from georgia_lynchings.rdf.sparql import SelectQuery
from georgia_lynchings.rdf.sparqlstore import SparqlStore

class QuerySet(object):
    '''An abstraction of a triplestore query focusing on
    :class:`~georgia_lynchings.rdf.models.ComplexObject` instances. Where
    :class:`~georgia_lynchings.rdf.sparql.SelectQuery` aims to be a general
    abstraction for all SPARQL SELECT queries, this class builds on top of
    those queries, exposing idioms as close as possible to those of
    :class:`~georgia_lynchings.rdf.models.ComplexObject`, to make it easier
    to build idiomatic queries for those complex objects.

    :param root_class: The :class:`~georgia_lynchings.rdf.models.ComplexObject`
                       subtype that serves as the root of the query. Queries
                       built from this query set will generally begin by
                       finding objects of this type.
    '''

    def __init__(self, root_class):
        self.root_class = root_class
        self.query_cache = None
        self.results_cache = None
        
    def __iter__(self):
        '''Iterate through the
        :class:`~georgia_lynchings.rdf.models.ComplexObject instances
        returned by this query set.'''
        if self.results_cache is None:
            self.results_cache = self._execute()
        return iter(self.results_cache)

    def __getitem__(self, i):
        '''Get a single :class:`~georgia_lynchings.rdf.models.ComplexObject`
        instance or slice of instances returned by this query set.'''
        # FIXME: Return an unevaluated QuerySet with appropriate OFFSET and
        # LIMIT instead of fetching the whole query set.
        if self.results_cache is None:
            self.results_cache = self._execute()
        return self.results_cache.__getitem__(i)

    def all(self):
        '''Get all of the objects represented by this query set.'''
        # nothing needed here currently. for now this is a convenience
        # method to make this class more approachable to people familiar
        # with django models.
        return self

    def _get_query(self):
        if self.query_cache is None:
            self.query_cache = self._make_query()
        return self.query_cache
    query = property(_get_query)
    '''The :class:`~georgia_lynchings.rdf.sparql.SelectQuery` used to fetch
    instances for this query set.'''

    def _make_query(self):
        '''Generate the SPARQL query used to fetch instances for this query
        set.'''
        q = SelectQuery(results=['obj'])
        if hasattr(self.root_class, 'rdf_type'):
            q.append((Variable('obj'), RDF.type, self.root_class.rdf_type))
        return q

    def _execute(self):
        '''Execute the SPARQL query for this query set, wrapping the results
        in appropriate :class:`~georgia_lynchings.rdf.models.ComplexObject`
        instances.'''
        store = SparqlStore()
        result_bindings = store.query(sparql_query=unicode(self.query))
        return [self.root_class(b['obj'])
                for b in result_bindings]


class QuerySetDescriptor(object):
    # ultimately this should grow into something like a django.db.Manager.
    # for now it's just a descriptor for easily creating QuerySet objects.
    def __get__(self, obj, cls):
        return QuerySet(root_class=cls)
