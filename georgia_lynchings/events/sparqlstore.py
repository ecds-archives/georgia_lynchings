'''
Objects to interact with the Sesame Triplestore in order to
run SPARQL queries against the georgia_lynchings content.

'''
from django.conf import settings
import httplib2
import json
import logging
import re
from pprint import pprint
from urllib import urlencode
import xml.dom.minidom
from xml.dom.minidom import Node

logger = logging.getLogger(__name__)

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
    def __init__(self, url=settings.SPARQL_STORE_API_TEST, repository=settings.SPARQL_STORE_REPOSITORY_TEST):
        self.url = url
        self.repository = repository 
        logger.debug("SesameConnection begin")
        logger.debug("url = [%s]" % self.url)      
        logger.debug("repository = [%s]" % self.repository)
        logger.info('SesameConnection starting up...\n')

    def close(self):
        logger.info('...SesameConnection closing down.\n')
        
    def getResultType(self, type):
        if type=='SPARQL_XML':  return 'application/sparql-results+xml'
        elif type=='SPARQL_JSON':  return 'application/sparql-results+json' 
        elif type=='BINARY_TABLE':  return 'application/x-binary-rdf-results-table' 
        elif type=='BOOLEAN':  return 'text/boolean'

    def query(self, result_type="SPARQL_XML", request_method="POST", sparql_query=None, output=None):
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
            # remove any newlines from sparql_query string
            sparql_query = sparql_query.translate(None,'\n')
            # add query to params              
            params = { 'query': sparql_query }            
            endpoint += "/%s" % (self.repository)
        else: 
            '''If no query is defined, an api call will be made
               to list the triplestore repositories available.'''
            params = {}                            
            request_method = 'GET'
            
        logger.debug('query %s to %s' % (request_method, endpoint))
        
        try:
            # send the query to the api
            (response, content) = self.doRequest(endpoint, request_method, params, headers) 

            # Output the xml to a file 
            if output:
                try:
                    a = open("/tmp/query_output.xml", 'w')
                    a.write(content) 
                except IOError as (errno, strerror):
                    logger.error("I/O error({0}): {1}".format(errno, strerror))
                    logger.error("Failed to open query output file.")
                    return
            
            # output the full response for now
            #pprint(response)
            logger.debug("Content Length = %s" % (len(content)))          
                    
            if (response.status == 200):
                'HTML Response OK'
                if (result_type == 'SPARQL_XML'):
                    'XML Results Output'    
                    logger.debug("Result type is SPARQL_XML, before call to Xml2Dict")             
                    return self.Xml2Dict(content)                  
                elif (result_type == 'SPARQL_JSON'):
                    'JSON Results Output'
                    logger.debug("Result type is SPARQL_JSON")                  
                    return json.loads(content)
            else:
                'HTML Response not OK'      
                logger.error('HTTP Response error code: %s' % response.status)            
                match = re.search(r'<b>message</b> <u>([^<]+)<', content)            
                if match:
                    logger.error('HTTP Response error message = [%s]' % match.group(1))      
                match = re.search(r'<b>description</b> <u>([^<]+)<', content)            
                if match: 
                    error_desc='raise Exception description = [%s]' % match.group(1)
                    logger.error(error_desc)
                    raise SparqlStoreException(error_desc)
                else:
                    logger.error('HTTP Response failed with response code = [%s]' % response)
                    logger.error('raise Exception [%s]' % content)
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

    def Xml2Dict(self, content):
        '''Parse the SPARQL query result content into a dictionary.'''
        doc = xml.dom.minidom.parseString(content)
        mapping=[]

        for node in doc.getElementsByTagName("result"):
            binding={}
            L2 = node.getElementsByTagName("binding")
            for node2 in L2:
                item={}
                key1 = node2.getAttribute("name")
                if (node2.getElementsByTagName("uri")): 
                    item['type']="uri"
                    
                elif (node2.getElementsByTagName("literal")):
                    item['type']="literal"
                    type2 = "literal"
                    if node2.getAttribute("datatype"):
                        logger.debug("Found a datatype")
                        item['datatype']=node2.getAttribute("datatype")
                        
                L3=node2.getElementsByTagName(item['type'])
                for node3 in L3:
                    value = ""
                    for node4 in node3.childNodes:
                        if node4.nodeType == Node.TEXT_NODE:
                            value += node4.data
                            item['value']=value
                binding[key1]=item
            mapping.append(binding)     
        return mapping

