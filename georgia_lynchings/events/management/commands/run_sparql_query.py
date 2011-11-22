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
        
        if not hasattr(settings, 'SPARQL_STORE_API') or not settings.SPARQL_STORE_API:
            raise CommandError('SPARQL_STORE_API must be configured in localsettings.py')
        if not hasattr(settings, 'SPARQL_STORE_REPOSITORY') or not settings.SPARQL_STORE_REPOSITORY:
            raise CommandError('SPARQL_STORE_REPOSITORY must be configured in localsettings.py')
            
        self.output = True if 'output' in options.keys()  and options['output'] else None
        self.list_repos = True if 'list_repos' in options.keys()  and options['list_repos'] else None
        self.ppdict = True if 'ppdict' in options.keys()  and options['ppdict'] else None
        self.query_key = True if 'query_key' in options.keys()  and options['query_key'] else None 
        self.query_file = True if 'query_file' in options.keys()  and options['query_file'] else None                            
                      
        self.query=None       
        if self.query_key:
            'Use one of the predefined sparql queries bases on given key.'
            logger.debug("QUERY KEY=[%s]" % options['query_key'])
            self.query=canned_sparql_queries.test_sparql_query[options['query_key']]           

        elif self.query_file:
            'Load the sparql query from the given file.'
            logger.debug("QUERY FILE=[%s]" % options['query_file'])
            try:
                self.query=open(options['query_file'], 'rU').read()
            except IOError as (errno, strerror):
                raise CommandError("Failed to read query file [%s]" % options['query_file']) 
                
        elif self.list_repos:
            'Query for a list of available repositories.'
            self.query=None                 
                        
        else:
            'No query given, so get a list of the repositories in the triplestore.'
            logger.debug("No options, get list of repositories.")

        # Run the SPARQL query
        self.result = self.runQuery()
        self.processResult(self.result, self.list_repos, self.ppdict)
        
    def runQuery(self):
        print "--------09---------------"        
        ss=SparqlStore()
        result={}
        try:
            if self.query: # Run the defined sparql query           
                result = ss.query("SPARQL_XML", "POST", self.query, self.output)
            elif self.list_repos: # Query the triplestore for available repositories
                result = ss.query("SPARQL_XML", "GET", None, self.output)
            else: logger.error('Query not found.')  # Error: Query not found.
        except: CommandError("Failed to run SparqlStore query.")  
        return result  
        
    def processResult(self, result=None, list_repos=None, ppdict=None):       
        if result:
            logger.debug("Result set size = [%d]" % len(result))
            # For the Repository list, skip pprint dict, and just print the list.
            if list_repos:               
                repo_list=[]
                for item in result:
                    repo_list.append(item['id']['value']);
                self.stdout.write("Repository List = [%s]" % repo_list)                    
            # Pretty print the dictionary to the console, if option is set.                
            elif ppdict:               
                self.stdout.write("\nPrettyPrint output to command line.\n")
                pprintfile = open("/tmp/georgia_lynchings_pprint_output.txt", 'w')
                pprint(result, pprintfile)
        else: self.stdout.write("\nResult does not exist.\n")       
