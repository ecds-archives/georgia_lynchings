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
    "The main class for communicating with a Sesame SPARQL endpoint."

    def __init__(self, url=None, repository=None):
        if not url:
            if not hasattr(settings, 'SPARQL_STORE_API') or not settings.SPARQL_STORE_API:
                raise SparqlStoreException('SPARQL_STORE_API must be configured in settings')
            url = settings.SPARQL_STORE_API
        if not repository:
            if not hasattr(settings, 'SPARQL_STORE_REPOSITORY') or not settings.SPARQL_STORE_REPOSITORY:
                raise SparqlStoreException('SPARQL_STORE_REPOSITORY must be configured in settings')
            repository = settings.SPARQL_STORE_REPOSITORY

        self.url = url
        self.repository = repository
       
    def query(self, sparql_query, initial_bindings={}):
        'Send a SPARQL query to the triplestore'
        logger.info('query: %r; bindings=%r' % (sparql_query, initial_bindings))

        query_params = dict((self._massage_into_binding(key), val)
                            for key, val in initial_bindings.items())
        query_params['query'] = sparql_query

        try:
            # send the query to the api
            (response, content) = self._execute_remote_query(query_params)

            if (response.status == 200):
                results = self._parse_xml_results(content)
                logger.debug("query returned %d results" % (len(results),))
                return results
            else:
                logger.error('HTTP Response error code: %s' % response.status)            
                raise self._parse_error(content)
        except httplib2.ServerNotFoundError:
            raise SparqlStoreException("Site is Down: %s" % self.url)                                             

    def _massage_into_binding(self, var):
        return '$' + (var[1:] if var.startswith('?') else var)
        
    def _execute_remote_query(self, params):
        endpoint = "%s/repositories/%s" % (self.url, self.repository)
        headers = {
          'content-type': 'application/x-www-form-urlencoded',
          'accept': 'application/sparql-results+xml',
        }
        (response, content) = httplib2.Http().request(endpoint, 'POST', urlencode(params), headers=headers)
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

    # error handling

    def _parse_error(self, content):
        '''Try to parse the server response into a sensible exception.'''
        match = re.search(r'<b>message</b> <u>([^<]+)<', content)            
        if match:
            logger.error('HTTP query response error message = [%s]' % match.group(1))      
        match = re.search(r'<b>description</b> <u>([^<]+)<', content)            
        if match: 
            error_desc='error description = [%s]' % match.group(1)
            logger.debug(error_desc)
            return SparqlStoreException(error_desc)
        else:
            logger.debug("couldn't find error description; error text = [%s ...]" % content[:50])  # only show first 50 chars
            return SparqlStoreException(content)
