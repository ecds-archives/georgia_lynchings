'''
**run_sparql_query** is a manage.py script to send SPARQL queries 
to the triplestore using the API

Examples usage
^^^^^^^^^^^^^^

Run help to see a list of keys available for the canned_sparql_queries::

  $ python manage.py run_sparql_query -h
  
Get a list of available repositories from the triplestore::

  $ python manage.py run_sparql_query -l

Run a SPARQL query from the canned_sparql_queries::

  $ python manage.py run_sparql_query -q find_event_order_location
  $ python manage.py run_sparql_query -q find_events_for_specific_person
  $ python manage.py run_sparql_query -q find_articles_for_event
  
Run a SPARQL query loaded from a file::

  $ python manage.py run_sparql_query -f events/management/commands/load_sparql_query.txt
  
Run a SPARQL query, send the xml response output the query_output.xml file::

  $ python manage.py run_sparql_query -l -o
  
Run a SPARQL query, pretty print the response parsed into a dictionary to the console::

  $ python manage.py run_sparql_query -l -p  

----
'''

from datetime import datetime
import logging
from optparse import make_option
from pprint import pprint
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from georgia_lynchings.events.sparqlstore import SparqlStore
import canned_sparql_queries

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    'Run a SPARQL query against the triplestore.'
    help = __doc__
    
    query_key_help='Load sparql query predefined query keys:\n%s\n' % canned_sparql_queries.test_sparql_query.keys()
        	
    # Query make be defined as key to predefined queries, or file containing query.
    option_list = BaseCommand.option_list + (
        make_option('--list_repos', '-l', help='Get a list of available repositories', action='store_true'),     
        make_option('--query_key', '-q', help=query_key_help, dest='query_key',
                    choices=canned_sparql_queries.test_sparql_query.keys()),    
        make_option('--query_file', '-f', help='Load sparql query from file', dest='query_file'),
        make_option('--output', '-o', help='Output will be saved to a file', default=None, action='store_true'),
        make_option('--ppdict', '-p', help='Pretty print the resulting dictionary', default=False, action='store_true'),        
     )
    help = 'Run SPARQL Query with query predefined or load query from file.'

    interrupted = False
    
    def handle(self,  *args, **options):
        
        query=None
        if options['query_key']:
            'Use one of the predefined sparql queries bases on given key.'
            logger.debug("QUERY KEY=[%s]" % options['query_key'])
            query=canned_sparql_queries.test_sparql_query[options['query_key']]           

        elif options['query_file']:
            'Load the sparql query from the given file.'
            logger.debug("QUERY FILE=[%s]" % options['query_file'])
            try:
                query=open(options['query_file'], 'rU').read()
            except IOError as (errno, strerror):
                logger.error("I/O error({0}): {1}".format(errno, strerror))
                logger.error("Failed to read query file [%s]" % options['query_file'])
                return
                
        elif options['list_repos']:
            'Query for a list of available repositories.'
            query=None                 
                        
        else:
            'No query given, so get a list of the repositories in the triplestore.'
            logger.debug("No options, get list of repositories.")

        # Open the SparqlStore
        try:  ss=SparqlStore()
        except: logger.error("Failed to load SparqlStore.")  
            
        # Run the SPARQL query
        result={}
        try:
            output = True if options['output'] else None
            if query: # Run the defined sparql query
                result = ss.query("SPARQL_XML", "POST", query, output)
            elif options['list_repos']: #Query the triplestore for available repositories
                result = ss.query("SPARQL_XML", "GET", None, output)
            else: logger.error('Query not found.')  # Error: Query not found.
        except: logger.error("Failed to run SparqlStore query.")
        
        if result:
            logger.debug("Result set size = [%d]" % len(result))
            # For the Repository list, skip pprint dict, and just print the list.
            if options['list_repos']:
                repo_list=[]
                for item in result:
                    repo_list.append(item['id']['value']);
                logger.info("Repository List = [%s]" % repo_list)
            # Pretty print the dictionary to the console, if option is set.                
            elif options['ppdict']: pprint (result)
