'''Tools for programmatic generation of SPARQL queries.

>>> from rdflib import Variable, RDF, RDFS
>>> q = SelectQuery(results=['prop', 'label'])
>>> q.append((Variable('prop'), RDF.type, RDF.Property))
>>> q.append((Variable('prop'), RDFS.label, Variable('label')))
>>> print q.as_sparql(pretty=True)
SELECT ?prop ?label
WHERE {
  ?prop <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/1999/02/22-rdf-syntax-ns#Property> .
  ?prop <http://www.w3.org/2000/01/rdf-schema#label> ?label .
}
>>> print q
SELECT ?prop ?label WHERE { ?prop <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/1999/02/22-rdf-syntax-ns#Property> . ?prop <http://www.w3.org/2000/01/rdf-schema#label> ?label . }
'''

from rdflib import Variable

__all__ = [ 'SelectQuery' ]

def _massage_into_variable(var):
    '''Wrap a single object in a :class:`rdflib.Variable` object if it
    isn't already one.
    '''

    if isinstance(var, Variable):
        return var
    else:
        return Variable(var)


class SelectQuery(object):
    '''A SPARQL SELECT query to aid in programmatic query construction.
    
    :param results: a list of variables to return from the query, specified
                    either as strings or :class:`rdflib.Variable` objects
    '''

    def __init__(self, results=None):
        if results is None:
            results = []
        self.result_variables = [ _massage_into_variable(res)
                                  for res in results ]
        self.graph = GraphPattern()

    def __unicode__(self):
        return self.as_sparql()

    def __str__(self):
        return self.__unicode__().encode()

    def as_sparql(self, pretty=False):
        '''Serialize the query for passing to a SPARQL server.
        
        :param pretty: boolean, add linebreaks and indentation
        '''

        if isinstance(pretty, bool):
            pretty = SparqlPrettyfier.from_bool(pretty)

        result_variables = self._result_variables_as_sparql()
        graph_pattern = self.graph.as_sparql(pretty)
        
        return u'SELECT %s%sWHERE %s' % (
            result_variables, pretty.line_break, graph_pattern)

    def _result_variables_as_sparql(self):
        'Encode query result variables.'

        if not self.result_variables:
            return u'*'

        vars = [ var.n3() for var in self.result_variables ]
        return u' '.join(vars)

    def append(self, pattern, optional=False):
        '''Append a single triple to the query graph.
        
        :param pattern: a graph pattern. Typically a tuple with 3 elements:
                        the subject, predicate and object. Each should be a
                        :class:`rdflib.URIRef`, :class:`rdflib.Literal`, or
                        :class:`rdflib.Variable`, or else it must provide a
                        compatible ``n3()`` method. Though this is typically
                        a tuple, it may instead be a :class:`GraphPattern`
                        or :class:`Triple` or any other object with a
                        :meth:`GraphPattern.as_sparql` method matching their
                        interface.
        :param optional: wrap the pattern in an OPTIONAL graph before
                         appending.
        '''
        if optional:
            subgraph = GraphPattern(optional=True)
            subgraph.append(pattern)
            self.graph.append(subgraph)
        else:
            self.graph.append(pattern)


def _massage_into_sparql(node):
    '''Wrap a node in a pattern compatible with :class:`SelectQuery` and
    :class:`GraphPattern` serialization. For now, if it as an ``as_sparql``
    method then just return it, otherwise try to wrap it in a
    :class:`Triple`.'''

    if hasattr(node, 'as_sparql'):
        return node
    else:
        # hope it's a tuple representing a triple
        return Triple(node)


class GraphPattern(object):
    '''A graph pattern in a SPARQL query, required by default but
    potentially optional. Callers can :meth:`append` other arbitrary
    patterns, including subordinate :class:`GraphPattern` objects and
    :class:`Triples`.'''

    def __init__(self, optional=False):
        self.patterns = []
        self.optional = optional

    def append(self, pattern):
        '''Append a single pattern (triple or subordinate graph pattern) to
        this graph pattern.'''
        self.patterns.append(_massage_into_sparql(pattern))

    def as_sparql(self, pretty):
        '''Serialize this graph pattern as for a SPARQL query.

        :param pretty: a :class:`SparqlPrettyfier` object or
                       interface-equivalent stand-in. Used for selecting
                       whitespace for pretty- or terse-printing.
        '''
        optional_str = u'OPTIONAL ' if self.optional else u''
        pattern_pretty = pretty.indent()
        patterns = [ pat.as_sparql(pattern_pretty) for pat in self.patterns ]
        patterns_str = pattern_pretty.line_break.join(patterns)
        return '%s%s{%s%s%s%s}' % (pretty.current_indent, optional_str, pretty.line_break,
                                   patterns_str,
                                   pretty.line_break, pretty.current_indent)


class Triple(object):
    '''A single triple pattern in a :class:`SelectQuery`.'''

    def __init__(self, items):
        self.subject, self.predicate, self.object = items

    def __str__(self):
        return self.__unicode__().encode()

    def __unicode__(self):
        return self.as_sparql(SparqlPrettyfier.from_bool(False))

    def as_sparql(self, pretty):
        '''Serialize this triple as for a SPARQL query.

        :param pretty: a :class:`SparqlPrettyfier` object or
                       interface-equivalent stand-in. Used for selecting
                       whitespace for pretty- or terse-printing.
        '''
        return u'%s%s %s %s .' % (pretty.current_indent,
            self.subject.n3(), self.predicate.n3(), self.object.n3())


class SparqlPrettyfier(object):
    '''Whitespace-aware serialization state for printing SPARQL queries.'''

    def __init__(self, line_break=u' ', indent_space=u'', indent_level=0):
        self.line_break = line_break
        self.indent_space = indent_space
        self.indent_level = indent_level

    def indent(self, add_level=1):
        '''Return a new :class:`SparqlPrettyfier`, but indented one step
        more than this one.
        '''
        cls = self.__class__
        return cls(line_break=self.line_break,
                   indent_space=self.indent_space,
                   indent_level=self.indent_level + add_level)

    @property
    def current_indent(self):
        '''the indent string at this indent level'''
        return self.indent_space * self.indent_level

    @classmethod
    def from_bool(cls, pretty):
        '''convenience method to return a prettyfier with default pretty or
        terse whitespace settings'''
        line_break = u'\n' if pretty else u' '
        indent_space = u'  ' if pretty else u''
        return cls(line_break, indent_space)
