from collections import defaultdict
import logging
from rdflib import Variable, RDF
from georgia_lynchings.rdf.fields import ChainedRdfPropertyField
from georgia_lynchings.rdf.sparql import SelectQuery, GraphPattern
from georgia_lynchings.rdf.sparqlstore import SparqlStore

logger = logging.getLogger(__name__)

def _massage_into_variable_name(var):
    '''Take a string that could be a variable name or a
    :class:`~rdflib.Variable` object, and convert it to a basic string
    variable name.'''
    return var[1:] if var.startswith('?') else var

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

    # FIXME: add more documentation of how this class collects its
    # properties into queries

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
        need to be queried later for each object.

        Specify chains of properties by joining the property names with a
        double underscore. For instance, if you could access
        ``myobj.foo.bar`` on a result object, you can pre-fetch that field
        with the field name ``foo__bar``.
        '''
        new_qs = self._copy()
        for field_name in fields:
            new_qs._add_extra_field(field_name)
        return new_qs

    def _add_extra_field(self, name):
        '''Look up the field named ``name``--or a whole double underscore
        separated chain of fields--on the query set result object type, and
        record all the information necessary to fetch them.
        '''
        # split the field chain on __ and store the entire field path in
        # self.extra_fields. for instance, if the user requests
        # foo__bar__baz, store: {
        #    'foo': [foo],
        #    'foo_bar': [foo, bar],
        #    'foo_bar_baz': [foo, bar, baz]
        # }
        # where foo, bar, and baz are those properties on the respective
        # result subobjects. collecting the full chain here makes it easier
        # to generate and handle the query below. note that we treat a
        # single property, such as 'foo', as a chain containing only one
        # item.

        # we'll be collecting prefixes as we loop through the field chain.
        # start with some empty lists that we'll populate as we go along
        name_parts = name.split('__')
        name_prefix_parts = []
        path_prefix_parts = []
        relative_class = self.result_class
        new_fields = {}
        # then loop through the split-up name parts
        for name_part in name_parts:
            # get the field, erroring immediately if it doesn't exist
            field = getattr(relative_class, name_part, None)
            if field is None:
                raise AttributeError("'%s' object has no RDF property '%s'" %
                                     (relative_class.__name__, name_part))

            # add it to self.extra_fields
            this_field_name_parts = name_prefix_parts + [name_part]
            this_field_name = '__'.join(this_field_name_parts)
            this_field_path = path_prefix_parts + [field]
            self.extra_fields[this_field_name] = this_field_path

            # update the prefix lists to prepare for next iteration
            name_prefix_parts = this_field_name_parts
            path_prefix_parts = this_field_path
            relative_class = field.result_type

    def _get_base_query(self):
        if self.base_query_cache is None:
            self.base_query_cache = self._make_base_query()
        return self.base_query_cache
    base_query = property(_get_base_query)
    '''The :class:`~georgia_lynchings.rdf.sparql.SelectQuery` used to fetch
    instances for this query set.'''

    def _get_supplemental_queries(self):
        if self.supplemental_query_cache is None:
            self.supplemental_query_cache = self._make_supplemental_queries()
        return self.supplemental_query_cache
    supplemental_queries = property(_get_supplemental_queries)
    '''A list of :class:`~georgia_lynchings.rdf.sparql.SelectQuery` objects
    used for additional fields in this query set.'''

    ORIGIN_VAR = Variable('obj') # a query variable for the self.root_obj
    RESULT_VAR = Variable('result') # a query variable for result objects

    def _root_variable_name(self):
        '''Our queries always have primary result objects in RESULT_VAR. If
        there's a field_chain specified then we start the query at
        ORIGIN_VAR and navigate from that to RESULT_VAR. If there's no
        field_chain then we start the query at RESULT_VAR itself.
        '''
        return self.ORIGIN_VAR if self.field_chain else self.RESULT_VAR

    # high-level query-making functions

    def _make_base_query(self):
        '''Construct the base SPARQL query used for the list of objects
        returned and all direct properties (i.e., chains of single-value
        properties) accessible directly from the result objects.'''
        props = self._get_direct_properties()
        q = SelectQuery(results=[self.RESULT_VAR] + props.keys())
        self._add_result_part_to_query(q)
        self._add_properties_to_query(q, props)
        return q

    def _make_supplemental_queries(self):
        '''Generate SPARQL queries needed to fetch additional property
        values for the instances in this query set.'''
        # Currently this creates one additional supplemental query for each
        # prepopulated multi-valued field. Like the base query, each
        # supplemental query also selects all single-value field paths
        # accessible directly below its primary multi-valued field.
        props = self._get_multiple_properties()
        return [self._make_supplemental_multiple_query(name, field_path)
                for name, field_path in props.items()]

    def _make_supplemental_multiple_query(self, name, field_path):
        '''Generate a supplemental SPARQL query to fetch additional property
        values for a single multi-valued field for all returned objects.'''
        # get the extra properties that we'll be returning from this query
        props = self._get_direct_properties(name)

        # make the query
        q = SelectQuery(results=[self.RESULT_VAR, name] + props.keys())
        self._add_result_part_to_query(q)

        # Loop through the field path adding each field to the query in
        # turn. Note that each field is returned using its field name
        # (joined by double underscores) so that we can attach them to
        # actual objects when we get all our results together.
        base_var = self.RESULT_VAR
        field_path_parts = []
        field_name_parts = name.split('__')
        for name_part, field in zip(field_name_parts, field_path):
            field_path_parts = field_path_parts + [name_part]
            field_name = '__'.join(field_path_parts)
            field_var = Variable(field_name)
            field.add_to_query(q, base_var, field_var)

            base_var = field_var

        # and add to the query all of the single-value properties that are
        # directly accessible from this query's multi-value property.
        self._add_properties_to_query(q, props, name)
        return q

    # adding stuff to base and supplemental queries

    def _add_result_part_to_query(self, q):
        '''Add query graph patterns to a SPARQL SELECT query representing
        the path bits in self.field_chain. This effectively navigates us
        from ``?obj`` (``self.root_obj``) to an appropriate ``?result``
        inside the query.
        '''
        # First limit the query by the type of the root object. If
        # self.root_obj is set then this makes sure it's of the appropriate
        # type. If it's not then it starts the query with all objects of
        # that type.
        if hasattr(self.root_class, 'rdf_type'):
            root_var = self._root_variable_name()
            q.append((root_var, RDF.type, self.root_class.rdf_type))

        # and then add graph patterns to navigate through the field chain

        if not self.field_chain:
            return

        if len(self.field_chain) == 1:
            result_field = self.field_chain[0]
        else:
            # the logic for adding chains of properties is already in
            # ChainedRdfPropertyField, so create an ad hoc one for temporary
            # use here.
            result_field = ChainedRdfPropertyField(*self.field_chain)
        
        result_field.add_to_query(q, self.ORIGIN_VAR, self.RESULT_VAR)

    # finding and adding property chains for particular queries

    def _get_direct_properties(self, prefix=''):
        '''Collect the properties from ``self.extra_fields`` that we can
        query alongside the `prefix` variable. If `prefix` is the empty
        string (the default), then collect the properties that we can query
        from the base query. This consists of all single-value fields and
        field chains under that prefix.'''

        # if the caller requests prefix foo, then all its subortinate
        # properties start with foo__. if the caller requests '' then all
        # its subordinate properties start with '', which means check each
        # of the properties for direct accessibility
        if prefix:
            prefix_length = len(prefix.split('__'))
            prefix = prefix + '__'
        else:
            prefix_length = 0

        # return a subset of extra_fields. a field is accessible if it
        # begins with the requested prefix. it is *directly* accessible if
        # each of the fields after that prefix is single-valued. note that
        # multi-valued fields are handled by supplemental queries.
        return dict((name, field_path)
                    for name, field_path in self.extra_fields.items()
                    if name.startswith(prefix) and
                       all(not f.multiple for f in field_path[prefix_length:]))

    def _get_multiple_properties(self):
        '''Collect multi-valued properties from ``self.extra_fields``. Each
        of these requires a separate supplemental query to fetch.'''
        return dict((name, field_path)
                    for name, field_path in self.extra_fields.items()
                    if field_path[-1].multiple)

    def _add_properties_to_query(self, q, props, prefix=None):
        '''Add an optional graph pattern for each of the properties in
        `props`. This makes the query also pull each of the directly
        accessible properties (identified in _get_direct_properties) along
        with its primary results.'''

        # collect subgraphs so that we can add to them for subordinate
        # properties. for example, if we request ``foo__bar``, then we
        # always request ``foo`` first (as guaranteed by  _add_extra_field).
        # when this function adds ``foo`` to the graph, it stores it in
        # prop_graphs so that when we request ``foo__bar``, we can nest the
        # ``bar`` part inside of the ``foo`` part.
        prop_graphs = {}
        # if there's a prefix, then this is a supplemental query, and
        # everything under that prefix goes in the main query.
        if prefix:
            prop_graphs[prefix] = q

        # sorted to guarantee that the ``foo`` graph is generated before the
        # ``foo__bar`` graph so that we can nest ``foo__bar`` inside
        # ``foo``.
        prop_names = sorted(props.keys())
        for name in prop_names:
            # if this is a chain, get the graph that it nests inside
            base_graph = q
            base_name, _, simple_field_name = name.rpartition('__')
            if base_name:
                base_graph = prop_graphs[base_name]
                base_var = Variable(base_name)
            else:
                base_var = self.RESULT_VAR

            # and put it into an optional graph...
            field_path = props[name]
            simple_field = field_path[-1]
            field_graph = GraphPattern(optional=True)
            simple_field.add_to_query(field_graph, base_var, Variable(name))
            # ... inside the parent field graph
            base_graph.append(field_graph)
            prop_graphs[name] = field_graph

    # query execution and interpretation

    def _execute(self):
        '''Execute the SPARQL queries for this query set, wrapping the results
        in appropriate :class:`~georgia_lynchings.rdf.models.ComplexObject`
        instances.'''
        var_bindings = {}
        if self.root_obj:
            root = self._root_variable_name()
            var_bindings[root] = self.root_obj.uri.n3()

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
        res_name = _massage_into_variable_name(self.RESULT_VAR)
        # use defaultdict instead of regular dict to make lookup cleaner
        results = defaultdict(lambda: defaultdict(list))
        for rows in supplemental_bindings: # results of each query
            for row in rows:                # each row
                result_id = row[res_name]    # the item this row supplements
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
        result_name = _massage_into_variable_name(self.RESULT_VAR)
        result_id = bindings[result_name]
        supplemental_bindings = collated_bindings.get(result_id, {})

        # wrap the raw bindings in Python types appropriate to the fields
        # they represent.
        props = {}
        for field_name, field_path in self.extra_fields.items():
            if len(field_path) > 1: # FIXME: handle longer field_path
                continue
            field = field_path[0]
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


class QuerySetDescriptor(object):
    # ultimately this should grow into something like a django.db.Manager.
    # for now it's just a descriptor for easily creating QuerySet objects.
    def __get__(self, obj, cls):
        return QuerySet(root_class=cls, root_obj=obj)
