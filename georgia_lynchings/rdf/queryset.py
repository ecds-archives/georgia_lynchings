from rdflib import Variable, RDF
from georgia_lynchings.rdf.fields import ChainedRdfPropertyField
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
        'The class that querying starts from'
        self.result_class = root_class
        'The class of the objects that the query will return'
        self.field_chain = []
        '''A chain of :class:`~georgia_lynchings.rdf.fields.RdfPropertyField`
        objects to follow to get from root_class to result_class'''

        self.query_cache = None
        'A cache for the SPARQL query represented by this QuerySet'
        self.results_cache = None
        'A cache for the results returned by this QuerySet'

    def _copy(self):
        '''Make a semantically-correct copy of the current object, throwing
        away any cached queries or results. Used internally to provide
        safe copy/edit/return semantics without side effects in, e.g.,
        :meth:`__getattr__`.
        '''
        new_qs = QuerySet(self.root_class)
        new_qs.result_class = self.result_class
        new_qs.field_chain = list(self.field_chain)
        # never copy cache values
        return new_qs
        
    def __iter__(self):
        '''Iterate through the
        :class:`~georgia_lynchings.rdf.models.ComplexObject instances
        returned by this query set. Convenient not only for iterating
        through results, but also for forcing execution of a qs via, e.g.,
        `list(qs)`.'''
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

    def __getattr__(self, attr):
        '''Return a QuerySet that descends into subobjects along the
        property `attr` defined on the current result class. That is, if
        this QuerySet is returning Foo objects, and the Foo class has an RDF
        property bar, then `this_qs.bar` is a new QuerySet that returns
        bars.
        '''
        if attr not in self.result_class._fields:
            raise AttributeError("'%s' object has no RDF property '%s'" %
                                 (self.result_class.__name__, attr))
        field = self.result_class._fields[attr]
        new_qs = self._copy()
        new_qs.result_class = field.result_type
        new_qs.field_chain.append(field)
        return new_qs

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
        result_var = self._result_variable_name()
        q = SelectQuery(results=[result_var])
        self._add_rdf_type_part_to_query(q)
        self._add_result_part_to_query(q)
        return q

    def _add_rdf_type_part_to_query(self, q):
        '''Add query graph patterns to a SPARQL SELECT query to check
        RDF.type against any defined rdf_type on the root_class. In a
        single-object query this will verify that the object has the
        rdf_type defined in its Python class. In a multi-object query it
        will bind ?obj to all objects of that type.
        '''
        if hasattr(self.root_class, 'rdf_type'):
            q.append((Variable('obj'), RDF.type, self.root_class.rdf_type))

    def _add_result_part_to_query(self, q):
        '''Add query graph patterns to a SPARQL SELECT query representing
        the path bits in self.field_chain. This effectively navigates us
        from ?obj to an appropriate ?result inside the query.
        '''
        if not self.field_chain:
            return

        if len(self.field_chain) == 1:
            result_field = self.field_chain[0]
        elif len(self.field_chain) > 1:
            # the logic for adding chains of properties is already in
            # ChainedRdfPropertyField, so create an ad hoc one for temporary
            # use here.
            result_field = ChainedRdfPropertyField(*self.field_chain)
        
        result_field.add_to_query(q, Variable('obj'), Variable('result'))

    def _execute(self):
        '''Execute the SPARQL query for this query set, wrapping the results
        in appropriate :class:`~georgia_lynchings.rdf.models.ComplexObject`
        instances.'''
        store = SparqlStore()
        result_bindings = store.query(sparql_query=unicode(self.query))
        result_var = self._result_variable_name()
        return [self.result_class(b[result_var])
                for b in result_bindings]

    def _result_variable_name(self):
        '''Determine whether the result is in the query binding ?result or
        ?obj. Return the appropriate variable name as a string (without the ?).
        '''
        # The query starts at ?obj. Typically it will go through a
        # field_chain and the resultant object(s) will be returned in
        # ?result. If there's no field_chain, though, (e.g., for most all()
        # queries), then the result will be the ?obj that we started with.
        return 'result' if self.field_chain else 'obj'


class QuerySetDescriptor(object):
    # ultimately this should grow into something like a django.db.Manager.
    # for now it's just a descriptor for easily creating QuerySet objects.
    def __get__(self, obj, cls):
        return QuerySet(root_class=cls)
