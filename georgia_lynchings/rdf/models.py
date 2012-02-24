'''Tools for mapping object properties to RDF properties in SPARQL queries
against project data.

>>> from rdflib import RDFS
>>> from georgia_lynchings.rdf.ns import scxn, ssxn
>>> class MacroEvent(ComplexObject):
...     rdf_type = scxn.Macro_Event
... 
>>> mac = MacroEvent(12)
>>> mac.label
rdflib.term.Literal(u'Coweta')
>>> unicode(mac.label)
u'Coweta'
'''

import logging
from rdflib import URIRef, Variable, BNode, RDF
from georgia_lynchings.rdf.ns import dcx, scx, ssxn
from georgia_lynchings.rdf.queryset import QuerySetDescriptor
from georgia_lynchings.rdf.sparql import SelectQuery, GraphPattern, Union
from georgia_lynchings.rdf.sparqlstore import SparqlStore

__all__ = [ 'ComplexObject', 'RdfPropertyField', 'ReversedRdfPropertyField',
            'ChainedRdfPropertyField', ]

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

    def __get__(self, obj, owner):
        # per convention, return self when evaluated on the class
        if obj is None:
            return self
            
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
            reverse_property = ReversedRdfPropertyField(self.prop,
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
            reverse_property = RdfPropertyField(self.prop,
                    result_type=forward_class, multiple=True)
            setattr(self.result_type, self.reverse_field_name,
                    reverse_property)
            self.result_type._fields[self.reverse_field_name] = reverse_property


class ChainedRdfPropertyField(RdfPropertyField):
    '''An :class:`RdfPropertyField` that chains multiple properties
    together. When evaluated on a :class:`ComplexObject`, it will execute a
    single query that chains through a list of properties to reach its
    result.
    '''

    def __init__(self, *props):
        props = [self._massage_property(prop) for prop in props]
        # this is multiple if any of its constituent props is multiple
        multiple = any(prop.multiple for prop in props)
        result_type = props[-1].result_type

        super_init = super(ChainedRdfPropertyField, self).__init__
        super_init(prop=None, multiple=multiple, result_type=result_type)

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
            link_target = BNode()
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

    def __init__(self, *props):
        props = [self._massage_property(prop) for prop in props]

        super_init = super(UnionRdfPropertyField, self).__init__
        super_init(prop=None, multiple=True)

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


class ComplexObjectType(type):
    '''Metaclass for :class:`ComplexObject`. Translate bare RDF attributes
    on the class into :class:`RdfPropertyField` instances.
    '''

    def __new__(cls, name, bases, attrs):
        forward_attrs = {}
        fields = {}

        # no translation for rdf_type: this represents the rdf:type of
        # instances of this class
        if 'rdf_type' in attrs and \
                isinstance(attrs['rdf_type'], URIRef):
            rdf_type = attrs.pop('rdf_type')
            forward_attrs['rdf_type'] = rdf_type

        for attr, val in attrs.items():
            # if it's a bare URIRef
            if isinstance(val, URIRef):
                # then translate it to an RdfPropertyField
                val = RdfPropertyField(val)
            if isinstance(val, RdfPropertyField):
                fields[attr] = val
            forward_attrs[attr] = val

        forward_attrs['_fields'] = fields

        # create the class
        super_new = super(ComplexObjectType, cls).__new__
        new_class = super_new(cls, name, bases, forward_attrs)

        for attr, val in forward_attrs.items():
            if hasattr(val, 'add_reverse_property'):
                val.add_reverse_property(new_class)

        return new_class


class ComplexObject(object):
    '''A parent class for complex objects in the project. Complex objects
    are a concept imported from the source data: They're data structures
    with lots of other project data and structures attached. In our RDF
    representation of project data, they're all identified by URIs in a
    well-known project namespace, which is based on an ID in the source
    data.

    :param id: the numeric identifier of the object in the source data
    '''

    __metaclass__ = ComplexObjectType

    objects = QuerySetDescriptor()
    '''A :class:`~georgia_lynchings.rdf.queryset.QuerySet` representing
    objects of a referenced subclass.'''

    def __init__(self, id):
        if isinstance(id, URIRef):
            self.uri = id
            if unicode(id).startswith(unicode(dcx) + 'r'):
                self.id = unicode(id)[len(unicode(dcx))+1:]
            else:
                self.id = None
        else:
            self.id = id
            self.uri = dcx['r' + str(id)]

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.uri)

    label = dcx.Identifier
    'a human-readable label for this object'
    # Classes use the Name-URI for their rdf_type. So indexing that here
    # (instead of, for instance, just dcx.ComplexType) allows us to search
    # for thing by MyClass.rdf_type.
    complex_type = ChainedRdfPropertyField(dcx.ComplexType, scx['Name-URI'])
    'the name-based uri of the complex object type for this object'

    verified_semantic = ssxn.verifiedSC
    '''has the coded data for this object been manually reviewed for
    semantic consistency?'''
    verified_details = ssxn.verifiedIO
    '''has the coded data for this object been manually reviewed for
    detail accuracy?'''

    @classmethod
    def all_instances(cls):
        rdf_type = getattr(cls, 'rdf_type', dcx.Row)
        q = SelectQuery(results=['obj'])
        q.append((Variable('obj'), RDF.type, rdf_type))

        store = SparqlStore()
        bindings = store.query(sparql_query=unicode(q))
        return [cls(b['obj']) for b in bindings]

    def index_data(self):
        data = { 'uri': self.uri }

        if self.id:
            data['row_id'] = self.id

        complex_type = self.complex_type
        if complex_type:
            data['complex_type'] = complex_type

        label = self.label
        if label:
            data['label'] = label

        return data
