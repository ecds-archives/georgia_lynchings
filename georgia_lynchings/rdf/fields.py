import logging
from rdflib import Variable, BNode, RDF
from georgia_lynchings.rdf.sparql import SelectQuery, GraphPattern, Union
from georgia_lynchings.rdf.sparqlstore import SparqlStore

logger = logging.getLogger(__name__)

class RdfPropertyField(object):
    '''A Python `descriptor <http://docs.python.org/reference/datamodel.html#descriptors>`_
    for simple SPARQL querying based on a single RDF property.

    :param prop: the RDF property as a :class:`~rdflib.URIRef`
    :param result_type: the Python type of the object at the other end of
                        this property. If specified, an object of this type
                        will be constructed when the property is accessed.
                        This property will pass the result RDF node
                        (:class:`~rdflib.URIRef` instance,
                        :class:`~rdflib.Literal` instance, etc) to the
                        constructor. If unspecified, no such wrapping will
                        occur, and the property will return the RDF node
                        itself.
    :param multiple: If True, this returns a list of result_type.                        
    :param reverse_field_name: if specified with ``result_type``, create a
                               property on ``result_type`` named
                               ``reverse_field_name`` that reverses this
                               relationship.
    '''

    def __init__(self, prop, result_type=None, multiple=False,
                 reverse_field_name=None):
        self.prop = prop
        self.result_type = result_type
        self.multiple = multiple
        self.reverse_field_name = reverse_field_name
        self.name = None # typically overridden in ComplexObjectType.__new__

    def __get__(self, obj, owner):
        # per convention, return self when evaluated on the class
        if obj is None:
            return self

        # see if this value was acached at object creation
        if self.name and self.name in obj.extra_properties:
            return obj.extra_properties[self.name]
            
        # generate a sparql query for the data we want
        q = SelectQuery(results=['result'])
        if hasattr(obj, 'rdf_type'):
            q.append((Variable('obj'), RDF.type, obj.rdf_type))
        self.add_to_query(q, Variable('obj'), Variable('result'))

        # ask the default SparqlStore for that data
        store = SparqlStore()
        bindings = {'obj': obj.uri.n3()}
        logger.debug('Executing query: `%s`; bindings: `%r`' % (q, bindings))
        bindings = store.query(sparql_query=unicode(q),
                               initial_bindings=bindings)
        # and interpret and return the results
        if bindings:
            if self.multiple:                
                return([self.wrap_result(b['result']) for b in bindings])
            else:
                result = bindings[0]['result']
                return self.wrap_result(result)
        # else None

    def add_to_query(self, q, source, target):
        '''Add triples to a query graph pattern to represent this property.
        In the base class implementation this just means adding the single
        triple ``source property target.``. This method is provided first as
        a hook so that subclasses can define more complex ways to add
        themselves to a query graph pattern, and second so that other
        code can bypass the descriptor protocol to generically add
        this property to a query they're generating.

        :param q: a :class:`~georgia_lynchings.rdf.sparql.SelectQuery`
        :param source: an rdf node (often a :class:`~rdflib.Variable`)
        :param target: an rdf node (often a :class:`~rdflib.Variable`)
        '''
        q.append((source, self.prop, target))

    def wrap_result(self, result_val):
        '''Wrap the result of property evaluation in this property's
        `result_type`. This method is called internally by the descriptor
        logic and provided for subclass overriding.
        '''
        if self.result_type is not None:
            return self.result_type(result_val)
        else:
            return result_val

    def add_reverse_property(self, forward_class):
        if self.result_type and self.reverse_field_name:
            reverse_property = ReversedRdfPropertyField(self,
                    result_type=forward_class, multiple=True)
            setattr(self.result_type, self.reverse_field_name,
                    reverse_property)


class ReversedRdfPropertyField(RdfPropertyField):
    '''An :class:`RdfPropertyField` that operates in reverse. When evaluated
    on a :class:`ComplexObject`, it will look for statements whose object is
    that complex object, and it will return the subject of that statement.
    '''

    def add_to_query(self, q, source, target):
        if hasattr(self.prop, 'add_to_query'):
            # if the property is itself an RdfPropertyField then just tell
            # it to add itself in reverse. 
            self.prop.add_to_query(q, target, source)
        else:
            # otherwise assume it's just a plain RDF node and add it
            # directly to the graph.
            q.append((target, self.prop, source))

    def add_reverse_property(self, forward_class):
        if self.result_type and self.reverse_field_name:
            if hasattr(self.prop, 'add_to_query'):
                reverse_property = self.prop
            else:
                reverse_property = RdfPropertyField(self.prop,
                        result_type=forward_class, multiple=True)
            if reverse_property.result_type is None:
                reverse_property.result_type = forward_class
            if reverse_property.name is None:
                reverse_property.name = self.reverse_field_name
            setattr(self.result_type, self.reverse_field_name,
                    reverse_property)
            self.result_type._fields[self.reverse_field_name] = reverse_property


class ChainedRdfPropertyField(RdfPropertyField):
    '''An :class:`RdfPropertyField` that chains multiple properties
    together. When evaluated on a :class:`ComplexObject`, it will execute a
    single query that chains through a list of properties to reach its
    result.
    '''

    def __init__(self, *props, **kwargs):
        props = [self._massage_property(prop) for prop in props]
        # this is multiple if any of its constituent props is multiple
        multiple = any(prop.multiple for prop in props)
        result_type = props[-1].result_type

        super_init = super(ChainedRdfPropertyField, self).__init__
        super_init(prop=None, multiple=multiple, result_type=result_type,
                   **kwargs)

        self.props = props
        # TODO: support reverse_field_name

    def _massage_property(self, prop):
        '''Make this property into an :class:`RdfPropertyField` if it's not
        already one.'''
        if hasattr(prop, 'add_to_query'):
            return prop
        else:
            return RdfPropertyField(prop)

    def add_to_query(self, q, source, target):
        # Given a property chain of p1, p2, p3, we want to add:
        #   ?source p1 _:tmp1 .
        #   _:tmp1 p2 _:tmp2 .
        #   _:tmp2 p3 ?target .
        # To do this, for each statement but the last generate a bnode to
        # act as the object, and use the previous object in the chain as the
        # subject of the following one.
        link_source = source
        for prop in self.props[:-1]:
            # use a bnode here just to generate a random label for a
            # variable. we used to use a plain bnode for link_target, but
            # those break with chained union properties since bnodes don't
            # connect across the union's subgraph patterns.
            var_name = str(BNode())
            link_target = Variable(var_name)
            prop.add_to_query(q, link_source, link_target)
            # prepare for the next link
            link_source = link_target
        
        # And the final link just results in the original target
        prop = self.props[-1]
        prop.add_to_query(q, link_source, target)


class UnionRdfPropertyField(RdfPropertyField):
    '''An :class:`RdfPropertyField` that uses SQL UNION to join multiple
    properties or property chains together. When evaluaged on a
    :class:`ComplexObject`, it will execute a single query that returns all
    of the values from all its constituent properties. These properties may
    be simple RDF URIs, or they may be instances of
    :class:`RdfPropertyField` or any subclass or compatible type.
    '''

    def __init__(self, *props, **kwargs):
        props = [self._massage_property(prop) for prop in props]

        super_init = super(UnionRdfPropertyField, self).__init__
        super_init(prop=None, multiple=True, **kwargs)

        self.props = props
        # TODO: is it possible to support result_type and
        # reverse_field_name?

    def _massage_property(self, prop):
        '''Make this property into an :class:`RdfPropertyField` if it's not
        already one.'''
        if hasattr(prop, 'add_to_query'):
            return prop
        else:
            return RdfPropertyField(prop)

    def add_to_query(self, q, source, target):
        # Given union properties of p1, p2, and p3, we want to add:
        #   { ?source p1 ?target }
        #   UNION
        #   { ?source p2 ?target }
        #   UNION
        #   { ?source p3 ?target }
        # :class:`georgia_lynchings.rdf.sparql.Union` basically does this
        # for us automatically.
        subgraphs = [self._make_subgraph(prop, source, target)
                     for prop in self.props]
        q.append(Union(subgraphs))

    def _make_subgraph(self, prop, source, target):
        '''Generate a :class:`~georgia_lynchings.rdf.sparql.GraphPattern`
        for a single constituent property.'''
        g = GraphPattern()
        prop.add_to_query(g, source, target)
        return g
