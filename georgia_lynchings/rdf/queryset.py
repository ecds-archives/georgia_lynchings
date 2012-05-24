from collections import defaultdict
import logging

from django.core.exceptions import ObjectDoesNotExist

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

    def get(self, id):
        '''
        Get a single instance of a specific object or raise a DoesNotExist error if
        appropriate.

        :param id: Id number (usually row number) used in the object.
        '''
        cx_cls = self.root_class(id)
        if cx_cls.exists:
            return cx_cls
        raise ObjectDoesNotExist("No %s exists with id %s." % (cx_cls.__class__.__name__, id))

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

    ORIGIN_VAR = Variable('obj') # a query variable for the self.root_obj
    RESULT_VAR = Variable('result') # a query variable for result objects

    def _root_variable_name(self):
        '''Our queries always have primary result objects in RESULT_VAR. If
        there's a field_chain specified then we start the query at
        ORIGIN_VAR and navigate from that to RESULT_VAR. If there's no
        field_chain then we start the query at RESULT_VAR itself.
        '''
        return self.ORIGIN_VAR if self.field_chain else self.RESULT_VAR

    # query execution and interpretation

    def _execute(self):
        '''Execute the SPARQL queries for this query set, wrapping the results
        in appropriate :class:`~georgia_lynchings.rdf.models.ComplexObject`
        instances.'''
        query_plan = self._plan_queries()
        queries = self._get_queries(query_plan)
        raw_results = self._execute_queries(queries)
        grouped_results = self._group_results(raw_results, query_plan)
        return self._map_results(grouped_results)

    # get and execute queries

    # {'pre__target': ['pre__target__extra1', 'pre_target__extra2']}
    def _plan_queries(self):
        '''Group the requested fields according to which ones can be queried
        together. The queries are named after a target field, and all
        properties sharing a target field can be queried together.'''
        queries = defaultdict(list)
        queries[''] = [] # make sure queries[''] (the default query) is always around
        for field_name in self.extra_fields.keys():
            query = self._query_target_for_field(field_name)
            base_query = queries[query] # reference to force existence
            if query != field_name:
                base_query.append(field_name)
        return queries

    def _query_target_for_field(self, name):
        '''A multi-valued field requires its own query. Any single-valued
        field can be queried along with its nearest multi-valued
        ancestor.'''
        while name:
            field_path = self.extra_fields[name]
            field = field_path[-1]
            if field.multiple:
                return name
            name, _, drop = name.rpartition('__')
        return ''

    def _get_queries(self, query_plan):
        '''Get the set of actual queries that fetches the planned fields.'''
        queries = {}
        # this doesn't need to be sorted, but it makes logs easier to follow
        # when queries happen in predictable order
        for target_field in sorted(query_plan.keys()):
            extra_fields = query_plan[target_field]
            result = self._query_for_fields(target_field, extra_fields)
            queries[target_field] = result
        return queries

    # expose the queries as a list for convenient debugging
    def _get_queries_as_list(self):
        query_plan = self._plan_queries()
        queries = self._get_queries(query_plan)
        return [queries[name] for name in sorted(queries.keys())]
    queries = property(_get_queries_as_list)
    '''A list of the :class:`~georgia_lynchings.rdf.sparql.SelectQuery`
    objects used to fetch the data for this QuerySet'''

    def _query_for_fields(self, target_field, extra_fields):
        '''Get a single :class:`~georgia_lynchings.rdf.sparql.SelectQuery`
        to return the specified ``target_field``, binding optional
        ``extra_fields`` along the way if they're present. Arguments are
        assumed to be possible and come from a sensible query plan as
        produced by :meth:`_plan_queries`.
        '''
        target_query_fields = self._query_fields_for_target(target_field)
        q = SelectQuery(results=[self.RESULT_VAR] + target_query_fields + extra_fields)
        self._add_result_part_to_query(q)
        self._add_target_to_query(q, target_query_fields)
        self._add_extra_fields_to_query(q, extra_fields, target_field)
        return q

    def _query_fields_for_target(self, target_field):
        '''Return the field and all of its ancestors::

            >>> self._query_fields_for_target('a__b__c__d')
            ['a', 'a__b', 'a__b__c', 'a__b__c__d']
        '''
        if not target_field:
            return []
        target_parts = target_field.split('__')
        return ['__'.join(target_parts[:i+1])
                for i in range(len(target_parts))]

    def _add_result_part_to_query(self, q):
        '''Add query graph patterns to a SPARQL SELECT query representing
        the path bits in self.field_chain. This effectively navigates us
        from ``?obj`` (``self.root_obj``) to an appropriate ``?result``
        inside the query. The result represents the primary result object
        returned by the QuerySet.'''
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

    def _add_target_to_query(self, q, target_fields):
        '''Add query graph patterns to a SPARQL SELECT query representing
        navigation from the result as calculated by
        :meth:`_add_result_part_to_query` to a target field along a query
        path as returned by :meth:`_query_fields_for_target`. This finds the
        multi-valued propert value that serves as the target for this
        particular SelectQuery.'''
        last_field_var = self.RESULT_VAR
        for field_name in target_fields:
            field_path = self.extra_fields[field_name]
            field = field_path[-1]
            field_var = Variable(field_name)
            field.add_to_query(q, last_field_var, field_var)
            last_field_var = field_var

    def _add_extra_fields_to_query(self, q, extra_fields, target_field):
        '''Add optional query graph patterns to a SPARQL SELECT query
        representing navigation from a target field across requested extra
        fields. This finds the single-valued property values associated with
        this query.'''
        prop_graphs = {target_field: q}

        for field_name in sorted(extra_fields):
            base_name, _, simple_field_name = field_name.rpartition('__')
            base_graph = prop_graphs[base_name]
            base_var = Variable(base_name) if base_name else self.RESULT_VAR

            field_var = Variable(field_name)
            field_path = self.extra_fields[field_name]
            field = field_path[-1]
            field_graph = GraphPattern(optional=True)
            field.add_to_query(field_graph, base_var, field_var)

            base_graph.append(field_graph)
            prop_graphs[field_name] = field_graph

    def _execute_queries(self, queries):
        '''Execute a set of SPARQL SELECT queries as returned by
        :meth:`_get_queries`.'''
        # if this QuerySet starts from a root object, then bind that once
        # for all of the queries.
        var_bindings = {}
        if self.root_obj:
            root = self._root_variable_name()
            var_bindings[root] = self.root_obj.uri.n3()

        results = {}
        # this doesn't need to be sorted, but it makes logs easier to follow
        # when queries happen in predictable order
        for query_target in sorted(queries.keys()):
            q = queries[query_target]
            results[query_target] = self._execute_single_query(q, var_bindings)
        return results

    def _execute_single_query(self, q, var_bindings):
        '''Execute a single SPARQL query and return the results.'''
        q_str = unicode(q)
        logger.debug('Executing query: `%s`; bindings: `%r`' % 
                     (q_str, var_bindings))
        store = SparqlStore()
        bindings = store.query(sparql_query=q_str,
                initial_bindings=var_bindings)
        return bindings

    # group results

    # {('pre', res, pre): {'pre__target': [t1, t2]}, ('pre__target', res, pre, t1): {'pre__target__extra1': e1}}
    def _group_results(self, raw_results, query_plan):
        '''Each query's bindings represent properties on an object buried
        somewhere inside the actual result set. Using the ``query_plan`` for
        guidance about how the queries were organized, group all of the
        bindings into a big dictionary. The dictionary key represents a
        particular object found through a particular field path in the
        result set. Each object and subobject in the result set has a key in
        this dictionary. This method deals with the raw bindings from the
        results, grouping them according to the particular subobject they
        belong to.'''
        results = {}
        for query_target, extra_fields in query_plan.items():
            query_results = raw_results[query_target]
            self._group_single_results(results, query_target, extra_fields, query_results)
        return results

    def _group_single_results(self, results, query_target, extra_fields, query_results):
        '''Group all of the results from a single SPARQL query.'''
        for result in query_results:
            self._group_single_result(results, query_target, extra_fields, result)

    def _group_single_result(self, results, query_target, extra_fields, result):
        '''Group a single set of bindings (row) from a query. Each row
        represents a single object in a multi-valued query, plus all of the
        single-valued field data directly accesible from that object. Add
        that object's id to the object list property that requested it, and
        add any nested single-valued property data directly accessible from
        the object itself.'''
        target_var = query_target or str(self.RESULT_VAR)
        result_type, context_objs = self._get_result_key(query_target, result)
        if result_type not in results:
            results[result_type] = {}
        results_for_type = results[result_type]
        if context_objs not in results_for_type:
            results_for_type[context_objs] = {}
        results_for_objs = results_for_type[context_objs]
        if target_var not in results_for_objs:
            results_for_objs[target_var] = []
        results_for_objs[target_var].append(result[target_var])

        for field in extra_fields:
            if field in result:
                result_type, context_objs = self._get_result_key(field, result)
                if result_type not in results:
                    results[result_type] = {}
                results_for_type = results[result_type]
                if context_objs not in results_for_type:
                    results_for_type[context_objs] = {}
                results_for_objs = results_for_type[context_objs]
                results_for_objs[field] = result[field]

    def _get_result_key(self, field, result):
        '''Get the key that will be used for this object data inside the
        collected results. ``field`` is the field path used to access this
        value. ``result`` is the current bindings set (row) from the query.
        The key consists of the field path of the parent object and the ids
        of the nodes in that field path.'''
        # as a special case, top-level objects (the primary results of this
        # QuerySet) get an empty field. we use this to get these object in
        # mapping.
        if not field:
            return ('', ())

        field_parts = self._query_fields_for_target(field)
        prefixes = field_parts[:-1]
        last_prefix = prefixes[-1] if prefixes else ''

        append_field_names = [str(self.RESULT_VAR)] + prefixes
        return last_prefix, tuple(result[field] for field in append_field_names)

    # map results

    def _map_results(self, grouped_results):
        '''Recursively wrap the grouped raw data from ``grouped_results``
        (as returned by :meth:`_group_results` into Python data types
        defined in their respective fields.'''
        map_plan = self._plan_maps()
        base_results = grouped_results[''][()] # the special case from _get_result_key()
        return [self._map_result((base_obj,), grouped_results[''],
                                 map_plan[''], self.result_class,
                                 grouped_results, map_plan)
                for base_obj in base_results[self.RESULT_VAR]]


    # {'': {'foo': 'foo'}, 'foo': {'bar': 'foo__bar'}, 'foo__bar': {'baz': 'foo__bar__baz'}}
    def _plan_maps(self):
        '''Groups the requested nested field paths into a dictionary mapping
        parent object paths to a set of properties and the full field paths
        that fulfil those properties. We calculate this map once and refer
        to it throughout the recursive mapping process.'''
        maps = defaultdict(dict)
        for field_name in self.extra_fields.keys():
            prefix, _, property_name = field_name.rpartition('__')
            maps[prefix][property_name] = field_name
        return maps

    def _map_result(self, context_objs, field_context, field_map, result_type, grouped_results, map_plan):
        '''Wrap the single object represented by a ``grouped_results`` entry
        in its appropriate Python type, recursively wrapping subobjects
        along the way.'''
        # grab the field data (buried inside grouped_results) that applies
        # specifically to this object
        field_data = field_context.get(context_objs, {})
        context_obj = context_objs[-1]
        # our goal is to grab and map all of the properties that are going
        # to be wrapped up in this object.
        extra_properties = {}
        # the fields requested for this object are in field_map
        for subproperty_name, subfield_name in field_map.items():
            # for each subfield
            subproperty_data = field_data.get(subfield_name, None)
            subfield_path = self.extra_fields[subfield_name]
            subfield = subfield_path[-1]

            # make a function that will wrap a single value for this
            # subfield. this function could wrap it in a simple type
            # (integer, date, etc), or it could recursively call into
            # _map_result() to wrap it in a complex object type.
            wrap_value = self._make_subfield_wrap_value(context_objs,
                    subfield_name, grouped_results, map_plan)
            # and call it on the property value if it's a single-value
            # field, or on each item if it's multi-valued.
            # NOTE: the results grouping above made sure that query targets
            # were in lists and extra properties were single values; the
            # query planning made sure that multi-valued fields were query
            # targets and single-valued fields were extra properties.
            if subfield.multiple:
                if subproperty_data is None:
                    subproperty_data = []
                subproperty_value = [wrap_value(d) for d in subproperty_data]
            else:
                subproperty_value = wrap_value(subproperty_data)

            # collect this particular subproperty into our extra properties
            extra_properties[subproperty_name] = subproperty_value
        # and then wrap those up into our result object
        return result_type(context_obj, extra_properties=extra_properties)

    def _make_subfield_wrap_value(self, context_objs, subfield_name, grouped_results, map_plan):
        '''Return a function that will wrap a single raw data result in an
        appropriate Python object. For complex types this may recursively
        call :meth:`_map_result`.'''
        subfield_path = self.extra_fields[subfield_name]
        subfield = subfield_path[-1]
        # if we have a plan to map this subfield, then return a function
        # that recurses into _map_result(). otherwise return a function that
        # just wraps the data in a simple Python type.
        if subfield_name in map_plan:
            def _wrap_value(val):
                if val is not None:
                    context_subobjs = context_objs + (val,)
                    subfield_context = grouped_results[subfield_name]
                    return self._map_result(context_subobjs, subfield_context,
                            map_plan[subfield_name], subfield.result_type,
                            grouped_results, map_plan)
        else:
            def _wrap_value(val):
                return subfield.result_type(val) if subfield.result_type else val
        return _wrap_value


class QuerySetDescriptor(object):
    # ultimately this should grow into something like a django.db.Manager.
    # for now it's just a descriptor for easily creating QuerySet objects.
    def __get__(self, obj, cls):
        return QuerySet(root_class=cls, root_obj=obj)
