'''Tools for mapping object properties to RDF properties in SPARQL queries
against project data.

>>> from rdflib import RDFS
>>> from georgia_lynchings.rdf.ns import scx, ssx
>>> class MacroEvent(ComplexObject):
...     rdf_type = scx.r1
...     victim = ssx.r82
... 
>>> mac = MacroEvent(12)
>>> mac.label
u'Coweta (Sam Hose)'
>>> mac.victim
u'Sam Hose'
'''

from rdflib import URIRef, Variable, RDF
from georgia_lynchings.rdf.ns import dcx
from georgia_lynchings.rdf.sparql import SelectQuery
from georgia_lynchings.rdf.sparqlstore import SparqlStore

__all__ = [ 'ComplexObject' ]

class RdfPropertyField(object):
    '''A Python `descriptor <http://docs.python.org/reference/datamodel.html#descriptors>`_
    for simple SPARQL querying based on a single RDF property.

    :param prop: the RDF property as a :class:`~rdflib.URIRef`
    '''

    def __init__(self, prop):
        self.prop = prop

    def __get__(self, obj, owner):
        # per convention, return self when evaluated on the class
        if obj is None:
            return self

        # generate a sparql query for the data we want
        q = SelectQuery(results=['result'])
        if hasattr(obj, 'rdf_type'):
            q.append((Variable('obj'), RDF.type, obj.rdf_type))
        q.append((Variable('obj'), self.prop, Variable('result')))
        
        # ask the default SparqlStore for that data
        store = SparqlStore()
        bindings = store.query(sparql_query=unicode(q),
                               initial_bindings={'obj': obj.uri.n3()})

        # and interpret and return the results
        if bindings:
            # FIXME: for now assume one row and a literal value. can't
            # assume these for long.
            return bindings[0]['result']['value']
        # else None


class ComplexObjectType(type):
    '''Metaclass for :class:`ComplexObject`. Translate bare RDF attributes
    on the class into :class:`RdfPropertyField` instances.
    '''

    def __new__(cls, name, bases, attrs):
        forward_attrs = {}

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
                field = RdfPropertyField(val)
                forward_attrs[attr] = field
            else:
                # otherwise leave it alone
                forward_attrs[attr] = val

        # create the class
        super_new = super(ComplexObjectType, cls).__new__
        return super_new(cls, name, bases, forward_attrs)


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

    def __init__(self, id):
        self.id = id
        self.uri = dcx['r' + str(id)]

    label = dcx.Identifier
    'a human-readable label for this object'
