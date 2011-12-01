# file events/abstractquery.py
# 
#   Copyright 2011,2012 Emory University Libraries
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

'''Provides sparql approach to access sesame triplestore.

This module provides a way to construct a SPARQL 1.1 Query
http://www.w3.org/TR/sparql11-query

'''

''' Initial query to test (return 350 results)
SELECT DISTINCT *
WHERE {
  ?macro a scx:r1;                 
         dcx:Identifier ?melabel;
         sxcxcx:r61 ?event. 
} 
'''

from django.conf import settings
import logging
from pprint import pprint

from georgia_lynchings.events.sparqlstore import SparqlStore

logger = logging.getLogger(__name__)

class AbstractQueryException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
        
class Variable:
    def __init__(self, value):
        self.value=value
        self.value = ''.join(('?', self.value))           
    def __str__(self):
        return repr(self.value)
        
class AbstractQuery(object):
    "The main class for communicating with a Sesame Server."
    def __init__(self):
        logger.debug("AbstractQuery begin\n")  

    def close(self):
        logger.info('AbstractQuery close\n')
        
    def setQueryForm(self, value=None):
        'Set the query form. Must be one of the following:[SELECT, CONSTRUCT, ASK, DESCRIBE].'
        if value in ['SELECT', 'CONSTRUCT', 'ASK', 'DESCRIBE', None]: 
            self.queryform=value
        else: raise AbstractQueryException("QueryForm [%s] is not one of the accepted values[SELECT, CONSTRUCT, ASK, DESCRIBE]." % value)      
        return self.queryform         
        
    def setDistinct(self, value=False):
        'An optional modifier for Select query. Possible values: True/False'
        if (value==True or value==False): self.distinct = value
        else: raise AbstractQueryException("Invalid value for distinct: %s" % value)
        return self.distinct
        
    def setReduced(self, value=False):
        'An optional modifier for Select query. Possible values: True/False'
        if (value==True or value==False): self.reduced = value
        else: raise AbstractQueryException("Invalid value for reduced: %s" % value)
        return self.reduced
        
    def setLimit(self, value=None):
        'Restrict the number of solutions.'     
        try: 
            if value: self.limit=int(value)
            if value==0: self.limit=None
            if value is None: self.limit=None
        except: raise AbstractQueryException("LIMIT value must be an integer: %s" % value)
        return self.limit
        
    def setOffset(self, value=None):
        'Control where the solutions start from in the overall sequence of solutions.'     
        try: 
            if value: self.offset=int(value)
            if value==0: self.offset=None
            if value is None: self.offset=None
        except: raise AbstractQueryException("OFFSET value must be an integer: %s" % value)
        return self.offset  
        
    def setOrderBy(self, value=None):
        'Establishes the order of a solution sequence.'
        if isinstance(value, str) or value is None: 
            self.orderby=value
        else: raise AbstractQueryException("ORDER BY value must be a string: %s" % value)      
        return self.orderby

    def setGroupBy(self, value=None):
        'Divides the solution into groups of one or more solutions.'
        if isinstance(value, str) or value is None: 
            self.groupby=value
        else: raise AbstractQueryException("GROUP BY value must be a string: %s" % value)      
        return self.groupby
        
    def setHaving(self, value=None):
        'Conditions to filter the data, applied to result set entity.'
        if isinstance(value, str) or value is None: 
            self.having=value
        else: raise AbstractQueryException("HAVING value must be a string: %s" % value)      
        return self.having                                                          

    def toSPARQL(self, graph_patterns, query_form='SELECT',  
                    distinct=None, reduced=None, 
                    limit=None, offset=None, 
                    order_by=None, group_by=None, 
                    having=None):
        '''Create a SPARQL query to the triplestore
        
        :graph_patterns: Combination of the following 5 types of graph patterns:
            Basic_Graph     # triple(a, b, c)
            Group_Graph,    # anything in {}, may have a FILTER(condition)
            Optional_Graph, # OPTIONAL {}
            Union_Graph,    # UNION
            Graph_Graph,    # FROM NAMED, GRAPH        
        :query_form: (optional) query forms include [SELECT, CONSTRUCT, ASK, DESCRIBE]
            defaults to SELECT.
        :distinct: (optional) Modifier for Select query. Values: True/False 
            'SELECT' ( 'DISTINCT' | 'REDUCED' )?   
        :reduced: (optional) Modifier for Select query. Values: True/False 
            'SELECT' ( 'DISTINCT' | 'REDUCED' )?  
        :limit: (optional) Restrict the number of solutions.
        :offset: (optional) Control where the solutions start from in the overall sequence of solutions.
        :order_by: (optional) Establishes the order of a solution sequence.
        :group_by: (optional) Divides the solution into groups of one or more solutions, 
            with the same overall cardinality.
        :having: (optional) Evaluated using the same rules as FILTER().  Due to the logic position 
            in which the HAVING clause is evaluated, expressions projected by the SELECT clause 
            are not visible to the HAVING clause.                                              
        '''        
        
        logger.debug("toSPARQL begin ...")    

