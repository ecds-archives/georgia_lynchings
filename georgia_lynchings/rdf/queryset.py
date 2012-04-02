from collections import defaultdict
import logging
from rdflib import Variable, RDF
from georgia_lynchings.rdf.fields import ChainedRdfPropertyField
from georgia_lynchings.rdf.sparql import SelectQuery, GraphPattern
from georgia_lynchings.rdf.sparqlstore import SparqlStore

logger = logging.getLogger(__name__)

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
    :param root_obj: The :class:`~georgia_lynchings.rdf.models.ComplexObject`
                     instance (optional )that serves as the root of the
                     query.
    '''

    def __init__(self, root_class, root_obj=None):
        self.root_class = root_class
        'The class that querying starts from'
        self.root_obj = root_obj
        'The object that querying starts from'
        self.result_class = root_class
        'The class of the objects that the query will return'
        self.field_chain = []
        '''A chain of :class:`~georgia_lynchings.rdf.fields.RdfPropertyField`
        objects to follow to get from root_class to result_class'''
        self.extra_fields = {}
        'Extra fields to prefetch from result objects in the query'

        self.base_query_cache = None
        '''A cache for the SPARQL query represented by the objects in this
        QuerySet'''
        self.supplemental_query_cache = None
        '''A cache for additional SPARQL queries needed to supplement fields
        on the objects in this QuerySet'''
        self.results_cache = None
        'A cache for the results returned by this QuerySet'

    def _copy(self):
        '''Make a semantically-correct copy of the current object, throwing
        away any cached queries or results. Used internally to provide
        safe copy/edit/return semantics without side effects in, e.g.,
        :meth:`__getattr__`.
        '''
        new_qs = QuerySet(self.root_class, self.root_obj)
        new_qs.result_class = self.result_class
        new_qs.field_chain = list(self.field_chain)
        new_qs.extra_fields = self.extra_fields.copy()
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
        field = getattr(self.result_class, attr, None)
        if field is None:
            raise AttributeError("'%s' object has no RDF property '%s'" %
                                 (self.result_class.__name__, attr))

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

    def fields(self, *fields):
        '''Pre-fetch the named fields (from among fields defined on the
        current result type) when executing this query so that they do not
        need to be queried later for each object.'''
        new_qs = self._copy()
        new_fields = dict((field, self._find_field(field))
                          for field in fields)
        new_qs.extra_fields.update(new_fields)
        return new_qs

    def _find_field(self, field_name):
        field = getattr(self.result_class, field_name, None)
        if field is None:
            raise AttributeError("'%s' object has no RDF property '%s'" %
                                 (self.result_class.__name__, field_name))
        return field

    def _get_base_query(self):
        if self.base_query_cache is None:
            self.base_query_cache = self._make_base_query()
        return self.base_query_cache
    base_query = property(_get_base_query)
    '''The :class:`~georgia_lynchings.rdf.sparql.SelectQuery` used to fetch
    instances for this query set.'''

    def _make_base_query(self):
        '''Generate the SPARQL query used to fetch instances for this query
        set.'''
        result_var = self._result_variable_name()
        basic_property_vars = [name for name, field
                               in self.extra_fields.items()
                               if not field.multiple]
        q = SelectQuery(results=[result_var] + basic_property_vars)
        self._add_rdf_type_part_to_query(q)
        self._add_result_part_to_query(q)
        self._add_extra_field_parts_to_base_query(q)
        return q

    def _get_supplemental_queries(self):
        if self.supplemental_query_cache is None:
            self.supplemental_query_cache = self._make_supplemental_queries()
        return self.supplemental_query_cache
    supplemental_queries = property(_get_supplemental_queries)
    '''A list of :class:`~georgia_lynchings.rdf.sparql.SelectQuery` objects
    used for additional fields in this query set.'''

    def _make_supplemental_queries(self):
        '''Generate SPARQL queries needed to fetch additional property
        values for the instances in this query set. Currently this creates
        one additional supplemental query for each prepopulated multi-valued
        field.'''
        multiple_fields = dict((name, field) for name, field
                               in self.extra_fields.items()
                               if field.multiple)
        return [self._make_supplemental_multiple_query(name, field)
                for name, field in multiple_fields.items()]

    def _make_supplemental_multiple_query(self, name, field):
        '''Generate a supplemental SPARQL query to fetch additional property
        values for a single multi-valued field for all returned objects.'''
        result_var = self._result_variable_name()
        q = SelectQuery(results=[result_var, name])
        self._add_rdf_type_part_to_query(q)
        self._add_result_part_to_query(q)
        self._add_one_field_part_to_query(q, name, field, optional=False)
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

    def _add_extra_field_parts_to_base_query(self, q):
        '''Add OPTIONAL query graph patterns to a SPARQL SELECT query
        to pre-fetch extra single-valued fields as part of this query.
        '''
        for field_name, field in self.extra_fields.items():
            if not field.multiple: # multi-valued fields handled in suppl. queries
                self._add_one_field_part_to_query(q, field_name, field,
                                                  optional=True)

    def _add_one_field_part_to_query(self, q, field_name, field, optional):
        '''Add graph patterns to a query to navigate through a single field.'''
        result_name = self._result_variable_name()
        field_graph = GraphPattern(optional=optional)
        field.add_to_query(field_graph, Variable(result_name), Variable(field_name))
        q.append(field_graph)

    def _execute(self):
        '''Execute the SPARQL queries for this query set, wrapping the results
        in appropriate :class:`~georgia_lynchings.rdf.models.ComplexObject`
        instances.'''
        var_bindings = {}
        if self.root_obj:
            var_bindings['obj'] = self.root_obj.uri.n3()

        base_bindings = self._execute_single_query(self.base_query, var_bindings)
        supplemental_bindings = [self._execute_single_query(q, var_bindings)
                                 for q in self.supplemental_queries]
        collated_bindings = self._collate_bindings(supplemental_bindings)

        return [self._wrap_result_bindings(b, collated_bindings)
                for b in base_bindings]

    def _execute_single_query(self, q, var_bindings):
        '''Execute a single SPARQL query and return the results. Provided as
        a convenient logging hook.'''
        q_str = unicode(q)
        logger.debug('Executing query: `%s`; bindings: `%r`' % 
                     (q_str, var_bindings))
        store = SparqlStore()
        bindings = store.query(sparql_query=q_str,
                initial_bindings=var_bindings)
        return bindings

    def _collate_bindings(self, supplemental_bindings):
        '''Collect all of the supplemental query results into one big
        dict, keyed on object ids. The dict values are multi-value bindings
        for the object. In particular, each is a dict keyed on field name,
        The values of these sub-dicts are lists of bindings for that
        object in that property.'''
        obj_name = self._result_variable_name()
        # use defaultdict instead of regular dict to make lookup cleaner
        results = defaultdict(lambda: defaultdict(list))
        for rows in supplemental_bindings: # results of each query
            for row in rows:                # each row
                result_id = row[obj_name]    # the item this row supplements
                result_fields = results[result_id] # the fields for that item
                for name, val in row.items():  # each binding in that row
                    if name != result_id:       # skip the item id itself
                        result_fields[name].append(val)
        # whew. now results should contain all of the values from all of
        # the supplemental bindings.
        return results

    def _wrap_result_bindings(self, bindings, collated_bindings):
        '''Wrap a single row of result bindings from the base query in an
        object of the appropriate result type for the query. Supplement
        multi-valued field values with the results of the supplemental
        queries, as collated by :meth:`_collate_bindings`.'''

        # grab the particular part of the supplemental bindings that apply
        # to this particular object.
        result_var = self._result_variable_name()
        result_id = bindings[result_var]
        supplemental_bindings = collated_bindings.get(result_id, {})

        # wrap the raw bindings in Python types appropriate to the fields
        # they represent.
        props = {}
        for field_name, field in self.extra_fields.items():
            if field.multiple:
                raw_binding = supplemental_bindings[field_name]
                binding = [field.wrap_result(b) for b in raw_binding]
                props[field_name] = binding
            else:
                binding = bindings.get(field_name, None)
                if binding:
                    binding = field.wrap_result(binding)
                props[field_name] = binding

        return self.result_class(result_id, extra_properties=props)

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
        return QuerySet(root_class=cls, root_obj=obj)
