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
from rdflib import URIRef, Variable, RDF
from georgia_lynchings.rdf.ns import dcx, scx, ssxn
from georgia_lynchings.rdf.fields import RdfPropertyField, \
        ChainedRdfPropertyField
from georgia_lynchings.rdf.queryset import QuerySetDescriptor
from georgia_lynchings.rdf.sparql import SelectQuery
from georgia_lynchings.rdf.sparqlstore import SparqlStore

__all__ = [ 'ComplexObject' ]

logger = logging.getLogger(__name__)

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
            # if it's a bare URIRef then translate it to an RdfPropertyField
            if isinstance(val, URIRef):
                val = RdfPropertyField(val)
            # if it's an RdfPropertyField then name it and stash it for
            # _fields
            if isinstance(val, RdfPropertyField):
                val.name = attr
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

    def __init__(self, id, extra_properties=None):
        if extra_properties is None:
            extra_properties = {}

        if isinstance(id, URIRef):
            self.uri = id
            if unicode(id).startswith(unicode(dcx) + 'r'):
                self.id = unicode(id)[len(unicode(dcx))+1:]
            else:
                self.id = None
        else:
            self.id = id
            self.uri = dcx['r' + str(id)]

        # store properties already cached from earlier queries
        self.extra_properties = extra_properties

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
