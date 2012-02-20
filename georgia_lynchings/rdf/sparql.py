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

class SelectQuery(object):
    '''A SPARQL SELECT query to aid in programmatic query construction.
    
    :param results: a list of variables to return from the query, specified
                    either as strings or :class:`rdflib.Variable` objects
    '''

    def __init__(self, results=None):
        if results is None:
            results = []
        self.result_variables = [ self._massage_into_variable(res)
                                  for res in results ]
        self.patterns = []
        self.optpatterns = []         

    def _massage_into_variable(self, var):
        '''Wrap a single object in a :class:`rdflib.Variable` object if it
        isn't already one.
        '''

        if isinstance(var, Variable):
            return var
        else:
            return Variable(var)

    def _massage_into_triple(self, triple):
        '''Wrap a single tuple in a :class:`Triple` object if it
        isn't already one.
        '''

        if isinstance(triple, Triple):
            return triple
        else:
            return Triple(triple)

    def __unicode__(self):
        return self.as_sparql()

    def __str__(self):
        return self.__unicode__().encode()

    def as_sparql(self, pretty=False):
        '''Serialize the query for passing to a SPARQL server.
        
        :param pretty: boolean, add linebreaks and indentation
        '''

        line_break = u'\n' if pretty else u' '

        result_variables = self._result_variables_as_sparql()
        graph_pattern = self._patterns_as_sparql()
        
        # Add optional graphs
        for optpat in self.optpatterns:
            graph_pattern += self._format_optional_pattern(optpat)
                    
        return u'SELECT %s%sWHERE {%s%s%s}' % (
            result_variables, line_break,
            line_break, graph_pattern, line_break)

    def _result_variables_as_sparql(self):
        'Encode query result variables.'

        if not self.result_variables:
            return u'*'

        vars = [ var.n3() for var in self.result_variables ]
        return u' '.join(vars)

    def _patterns_as_sparql(self, pretty=False):
        'Encode the query main graph pattern.'

        patterns = [ unicode(pat) for pat in self.patterns ]
        return u' '.join(patterns)

    def _format_optional_pattern(self, optpat):
        'Encode the query main graph pattern.'   
        
        return u' OPTIONAL {%s%s%s} ' % (u' ', optpat, u' ')               

    def append(self, pattern, optional=None):
        '''Append a single triple to the query graph.
        
        :param pattern: a tuple with 3 elements: the subject, predicate and
                        object. Each should be a :class:`rdflib.URIRef`,
                        :class:`rdflib.Literal`, or
                        :class:`rdflib.Variable`, or else it must provide a
                        compatible ``n3()`` method.
        '''
        if optional:
            self.optpatterns.append(self._massage_into_triple(pattern))
        else:
            self.patterns.append(self._massage_into_triple(pattern))


class Triple(object):
    '''A single triple pattern in a :class:`SelectQuery`.'''

    def __init__(self, items):
        self.subject, self.predicate, self.object = items

    def __unicode__(self):
        return u'%s %s %s .' % \
            (self.subject.n3(), self.predicate.n3(), self.object.n3())

    def __str__(self):
        return self.__unicode__().encode()
