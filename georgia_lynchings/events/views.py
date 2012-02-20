import json
import logging
from pprint import pprint
import sunburnt
from urllib import quote
import urllib2
import simplejson

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe

from georgia_lynchings.events.models import MacroEvent, \
    get_all_macro_events, SemanticTriplet, get_filters
from georgia_lynchings.forms import SearchForm    
from georgia_lynchings.events.details import Details   
from georgia_lynchings.events.timemap import Timemap   

logger = logging.getLogger(__name__)

                        
def articles(request, row_id):
    '''
    List all articles for a
    :class:`~georgia_lynchings.events.models.MacroEvent`.
    
    :param row_id: the numeric identifier for the 
                   :class:`~georgia_lynchings.events.models.MacroEvent`.
    '''
    event = MacroEvent(row_id)
    resultSet = event.get_articles()
    if resultSet:      
        title = resultSet[0]['melabel']
        # create a link for the macro event articles
        for result in resultSet:
            # Clean up data, add "n/a" if value does not exist
            if 'docpath' in result.keys(): 
                # FIXME: find a better way to do this
                result['docpath_link'] = quote(result['docpath'].replace('\\', '/'))
                result['docpath'] = result['docpath'][10:] 
    else:   title = "No records found" 
    return render(request, 'events/articles.html',
                  {'resultSet': resultSet, 'row_id':row_id, 'title':title})
                  
def details(request, row_id):
    '''
    List details for a
    :class:`~georgia_lynchings.events.models.MacroEvent`.
    
    :param row_id: the numeric identifier for the 
                   :class:`~georgia_lynchings.events.models.MacroEvent`.
    '''
    
    # Get the details associate with this macro event.
    details = Details(row_id)
    results = details.get()
  
    if results:   
        title = row_id
        results['articles_link'] = reverse('articles', kwargs={'row_id': row_id})          
    else:   title = "No records found"  
     
    return render(request, 'events/details.html',
                  {'results': results, 'row_id':row_id, 'title':title})                   

    
def home(request):
    template = 'index.html'
    return render(request, template, {'search_form': SearchForm()})

def macro_events(request):
    '''List all macro events, provide article count.'''

    results = get_all_macro_events()
    if results:   title = "%d Macro Events" % len(results)
    else:   title = "No records found"      
    return render(request, 'events/macro_events.html',
                  {'results': results, 'title':title}) 

def search(request):
    '''Search for a term in macro events, and provide a list of matching
    events.'''

    term = ''
    results = []

    form = SearchForm(request.GET)
    if form.is_valid():
        solr = sunburnt.SolrInterface(settings.SOLR_INDEX_URL)
        term = form.cleaned_data['q']
        results = solr.query(term) \
                      .filter(complex_type=MacroEvent.rdf_type) \
                      .execute()

        for result in results:
            # For triplets on the event, we want a handful of triplets, with
            # preference given to ones that match the term. So: filter for
            # triplets (filter here instead of query to allow solr to cache
            # the triplets), query within those results for the macro event
            # (which returns all of the triplets for that event), and then
            # boost the ones that match the term to bring them to the top of
            # the list. Note that query() needs to come before filter()
            # because of the way sunburnt constructs its query.
            result['triplets'] = solr.query(macro_event_uri=result['uri']) \
                                     .filter(complex_type=SemanticTriplet.rdf_type) \
                                     .boost_relevancy(2, text=term) \
                                     .execute()

            # also grab the articles for display
            event = MacroEvent(result['row_id'])
            result['articles'] = event.get_articles()

    return render(request, 'events/search_results.html',
                  {'results': results, 'term': term, 'form': form})

#These views and variables are for Map display

# Create filters
filters = ['victim_allegedcrime_brundage']

def timemap(request):
    '''Send list of filters generated from :class:`~georgia_lynchings.events.timemap.Timemap`.
    '''

    # Get the json object require for displaying timemap data   
    timemap = Timemap(filters)
    timemap.get_json()

    return render(request, 'events/timemap.html', \
        {'filters' : get_filters(filters)})

def map_json(request):
    '''
    Returns json data from :class:`~georgia_lynchings.events.timemap.Timemap` for map display
    '''

    map_data = Timemap(filters)
    json_str = json.dumps(map_data.get_json(), indent=4)
    response = HttpResponse(json_str, mimetype='application/json')

    return response
