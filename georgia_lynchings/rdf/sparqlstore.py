'''
Objects to interact with the Sesame Triplestore in order to
run SPARQL queries against the georgia_lynchings content.

'''
import httplib2
import json
import logging
import re
from urllib import urlencode
from xml.dom import minidom

from django.conf import settings
from rdflib import URIRef, Literal, BNode

logger = logging.getLogger(__name__)

XML_NS = 'http://www.w3.org/XML/1998/namespace'

# FIXME: This module needs some general cleanup.

class SparqlStoreException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
        
class SparqlStore:
    "The main class for communicating with a Sesame Server."
    '''
    result_type: [SPARQL_XML|SPARQL_JSON]
    request_method: [GET|POST|...]
    query: sparql query string
    url: sparql store API URL
    repository: sparql store repository
    '''
    def __init__(self, url=None, repository=None):
        
        if url: self.url = url
        else:
            if not hasattr(settings, 'SPARQL_STORE_API') or not settings.SPARQL_STORE_API:
                raise SparqlStoreException('SPARQL_STORE_API must be configured in localsettings.py')
            else: self.url = settings.SPARQL_STORE_API
       
        if repository: self.repository = repository
        else:        
            if not hasattr(settings, 'SPARQL_STORE_REPOSITORY') or not settings.SPARQL_STORE_REPOSITORY:
                raise SparqlStoreException('SPARQL_STORE_REPOSITORY must be configured in localsettings.py')
            else: self.repository = settings.SPARQL_STORE_REPOSITORY 

        logger.debug("SesameConnection begin")    
        logger.debug("url = [%s]" % self.url)      
        logger.debug("repository = [%s]" % self.repository)

    def getResultType(self, type):
        if type=='SPARQL_XML':  return 'application/sparql-results+xml'
        elif type=='SPARQL_JSON':  return 'application/sparql-results+json' 
        elif type=='BINARY_TABLE':  return 'application/x-binary-rdf-results-table' 
        elif type=='BOOLEAN':  return 'text/boolean'

    def query(self, result_type="SPARQL_XML", request_method="POST",
              sparql_query=None, initial_bindings={}):
        'Send a SPARQL query to the triplestore'
        
        logger.debug("query begin ... result_type=[%s]" % result_type)

        # set the content-type and accept headers 
        headers = { 
          'content-type': 'application/x-www-form-urlencoded',      
          'accept': self.getResultType(result_type)
        }
        # create the endpoint      
        endpoint = "%s/repositories" % (self.url)
        logger.debug("query endpoint=[%s]" % endpoint)        
        
        if sparql_query:
            # add query to params              
            params = { 'query': sparql_query }            
            endpoint += "/%s" % (self.repository)
        else: 
            '''If no query is defined, an api call will be made
               to list the triplestore repositories available.'''
            params = {}                            
            request_method = 'GET'

        # add sesame initial query bindings
        binding_params = dict(('$' + key, val)
                               for key, val in initial_bindings.items())
        params.update(binding_params)
            
        logger.debug('query %s to %s' % (request_method, endpoint))
        
        try:
            # send the query to the api
            (response, content) = self.doRequest(endpoint, request_method, params, headers) 
            logger.debug("Response Status = %s" % (response.status))
            logger.debug("Content Length = %s" % (len(content)))                     
                    
            if (response.status == 200):
                'HTML Response OK'
                if (result_type == 'SPARQL_XML'):
                    'XML Results Output'    
                    logger.debug("Result type is SPARQL_XML, before call to _parse_xml_results")             
                    return self._parse_xml_results(content)                  
                elif (result_type == 'SPARQL_JSON'):
                    'JSON Results Output'
                    logger.debug("Result type is SPARQL_JSON")                  
                    return self._parse_json_results(content)
            else:
                'HTML Response not OK'      
                logger.warn('HTTP Response error code: %s' % response.status)            
                match = re.search(r'<b>message</b> <u>([^<]+)<', content)            
                if match:
                    logger.warn('HTTP Response error message = [%s]' % match.group(1))      
                match = re.search(r'<b>description</b> <u>([^<]+)<', content)            
                if match: 
                    error_desc='raise Exception description = [%s]' % match.group(1)
                    logger.warn(error_desc)
                    raise SparqlStoreException(error_desc)
                else:
                    logger.warn('HTTP Response failed with response code = [%s]' % response)
                    logger.warn('raise Exception [%s ...]' % content[:50])  # only show first 30 chars
                    raise SparqlStoreException(content)
        except httplib2.ServerNotFoundError:
            raise SparqlStoreException("Site is Down: %s" % self.url)                                             
        
    def doRequest(self, endpoint, request_method, params, headers):
        (response, content) = httplib2.Http().request(endpoint, request_method, urlencode(params), headers=headers)
        logger.debug('HTTP request endpoint=[%s]' % endpoint)
        logger.debug('HTTP request request_method=[%s]' % request_method)  
        logger.debug('HTTP request headers=[%s]' % headers) 
        logger.debug('HTTP response=[%s]' % response)
        return (response, content)

    # parse xml results

    def _parse_xml_results(self, content):
        '''Parse SPARQL XML query result contents into a list of result
        objects.'''
        doc = minidom.parseString(content)
        return [self._parse_result_node(res)
                for res in doc.getElementsByTagName('result')]

    def _parse_result_node(self, result_elem):
        '''Parse a single SPARQL XML query result node into a dict of
        bindings.'''
        return dict((self._parse_binding_node_name(b),
                     self._parse_binding_node_value(b))
                    for b in result_elem.getElementsByTagName('binding'))

    def _parse_binding_node_name(self, binding_elem):
        '''Get the name from a single SPARQL XML result binding.'''
        return binding_elem.getAttribute('name')

    def _parse_binding_node_value(self, binding_elem):
        '''Parse the value from a single SPARQL XML result binding as a
        :class:`rdflib.URIRef`, :class:`rdflib.Literal`, or
        :class:`rdflib.BNode`.'''
        uri_nodes = binding_elem.getElementsByTagName('uri')
        if uri_nodes:
            uri_node = uri_nodes[0]
            uri = self._parse_node_text(uri_node)
            return URIRef(uri)

        literal_nodes = binding_elem.getElementsByTagName('literal')
        if literal_nodes:
            literal_node = literal_nodes[0]
            # getAttribute returns '' for nonexistent attributes. use "or
            # None" here to replace '' (which is boolean false) with None so
            # that we don't try to construct this Literal with lang=''
            # and/or datatype='', which would be invalid.
            datatype = literal_node.getAttribute('datatype') or None
            language = literal_node.getAttributeNS(XML_NS, 'lang') or None
            value = self._parse_node_text(literal_node)
            return Literal(value, lang=language, datatype=datatype)

        bnode_nodes = binding_elem.getElementsByTagName('bnode')
        if bnode_nodes:
            bnode_node = bnode_nodes[0]
            label = self._parse_node_text(bnode_node)
            return BNode(label)

        # other types are invalid. return None for those, I guess?

    def _parse_node_text(self, node):
        '''Concatenate all of the text children for an XML node.'''
        return ''.join(child.nodeValue for child in node.childNodes)

    # parse json results

    def _parse_json_results(self, content):
        '''Parse SPARQL JSON query result contents into a list of result
        objects.'''
        body = json.loads(content)
        bindings = body['results']['bindings']
        return [self._parse_json_bindings(b) for b in bindings]

    def _parse_json_bindings(self, bind_dict):
        '''Parse a single SPARQL JSON result object into a dict of
        bindings.'''
        return dict((name, self._parse_json_binding_val(val))
                    for name, val in bind_dict.items())

    def _parse_json_binding_val(self, val_dict):
        '''Parse the value from a single SPARQL JSON result binding as a
        :class:`rdflib.URIRef`, :class:`rdflib.Literal`, or
        :class:`rdflib.BNode`.'''
        if val_dict['type'] == 'uri':
            return URIRef(val_dict['value'])

        if val_dict['type'] == 'literal':
            datatype = val_dict.get('datatype', None)
            language = val_dict.get('xml:lang', None)
            value = val_dict['value']
            return Literal(value, lang=language, datatype=datatype)

        if val_dict['type'] == 'bnode':
            return BNode(val_dict['value'])

        # other types are invalid. return None for those, I guess?
