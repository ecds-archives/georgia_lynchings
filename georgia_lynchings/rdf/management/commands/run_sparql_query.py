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

  $ python manage.py run_sparql_query -f rdf/management/commands/load_sparql_query.txt

----
'''

from datetime import datetime
import logging
from optparse import make_option
from pprint import pprint
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from georgia_lynchings.rdf.sparqlstore import SparqlStore
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
     )
    help = 'Run SPARQL Query with query predefined or load query from file.'

    interrupted = False
    
    def handle(self, query_file=None, **options):
                
        if not hasattr(settings, 'SPARQL_STORE_API') or not settings.SPARQL_STORE_API:
            raise CommandError('SPARQL_STORE_API must be configured in localsettings.py')
        if not hasattr(settings, 'SPARQL_STORE_REPOSITORY') or not settings.SPARQL_STORE_REPOSITORY:
            raise CommandError('SPARQL_STORE_REPOSITORY must be configured in localsettings.py')
            
        self.list_repos = True if 'list_repos' in options.keys()  and options['list_repos'] else None
        self.query_key = True if 'query_key' in options.keys()  and options['query_key'] else None                            
                      
        self.query=None       
        if self.query_key:
            'Use one of the predefined sparql queries bases on given key.'
            logger.debug("QUERY KEY=[%s]" % options['query_key'])
            self.query=canned_sparql_queries.test_sparql_query[options['query_key']]           

        elif query_file:
            'Load the sparql query from the given file.'
            logger.debug("QUERY FILE=[%s]" % query_file)
            try:
                self.query=open(query_file, 'rU').read()
            except IOError as (errno, strerror):
                raise CommandError("Failed to read query file [%s]" % query_file) 
                
        elif self.list_repos:
            'Query for a list of available repositories.'
            self.query=None
                        
        else:
            'No query given, so get a list of the repositories in the triplestore.'
            logger.debug("No options, get list of repositories.")

        # Run the SPARQL query
        self.result = self.runQuery()
        self.processResult(self.result, self.list_repos)
        print "\n\n"        
        pprint(self.result)
        print "\n\n"
        
    def runQuery(self):       
        ss=SparqlStore()
        result={}
        try:
            if self.query: # Run the defined sparql query           
                result = ss.query(result_type="SPARQL_XML", request_method="POST", sparql_query=self.query)
            elif self.list_repos: # Query the triplestore for available repositories
                result = ss.query(result_type="SPARQL_XML", request_method="GET", sparql_query=None)
            else: logger.error('Query not found.')  # Error: Query not found.
        except: CommandError("Failed to run SparqlStore query.")  
        return result  
        
    def processResult(self, result=None, list_repos=None):       
        if result:
            logger.debug("Result set size = [%d]" % len(result))
            # For the Repository list, skip pprint dict, and just print the list.
            if list_repos:               
                repo_list=[]
                for item in result:
                    repo_list.append(item['id']['value']);
                self.stdout.write("Repository List = [%s]" % repo_list)                    
        else: self.stdout.write("\nResult does not exist.\n")       
