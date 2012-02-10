import json
import logging
from pprint import pprint
import sunburnt
from urllib import quote
import urllib2

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe

from georgia_lynchings.events.models import MacroEvent, \
        get_events_by_locations, get_events_by_times, get_all_macro_events, \
        SemanticTriplet
from georgia_lynchings.forms import SearchForm        
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
    # set prev/next links
    # FIXME: this needs to be based on a defined set of actice macro events
    pagelink = {}    
    pagelink['prev']='../../%s/articles' % (int(row_id) - 1)    # FIXME: use reverse here
    pagelink['next']='../../%s/articles' % (int(row_id) + 1)    # FIXME: use reverse here 
    return render(request, 'events/articles.html',
                  {'resultSet': resultSet, 'row_id':row_id, 'title':title, 'pagelink':pagelink})
                  
def details(request, row_id):
    '''
    List details for a
    :class:`~georgia_lynchings.events.models.MacroEvent`.
    
    :param row_id: the numeric identifier for the 
                   :class:`~georgia_lynchings.events.models.MacroEvent`.
    '''
    results = {}
    pagelink = {}
    event = MacroEvent(row_id)
    results = event.get_details()
    # FIXME: this needs to be based on a defined set of actice macro events    
    pagelink['prev']='../../%s/details' % (int(row_id) - 1)   # FIXME: use reverse here
    pagelink['next']='../../%s/details' % (int(row_id) + 1)   # FIXME: use reverse here   
    if results:   
        title = row_id
        results['articles_link'] = '../../../events/%s/articles' % row_id
        # TODO: change old format of simplex victim to new format complex victims (multiple)
        results['victim'] = event.victim          
    else:   title = "No records found"    
    return render(request, 'events/details.html',
                  {'results': results, 'row_id':row_id, 'title':title, 'pagelink':pagelink})                   

def home(request):
    template = 'index.html'
    return render(request, template, {'search_form': SearchForm()})

def locations(request):
    '''List all events, ordered by their location.'''

    results = get_events_by_locations()
    return render(request, 'events/locations.html',
                  {'results': results})
                  
def times(request):
    '''List all events, provide the date range as mindate and maxdate.'''

    results = get_events_by_times()
    if results:   title = "%d Macro Events" % len(results)
    else:   title = "No records found"      
    return render(request, 'events/times.html',
                  {'results': results, 'title':title}) 
                  
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

#These views are for Map display
def timemap(request):
    '''Send timemap json data created from solr to the timemap template.
    '''

    # Create filters
    filters = ['victim_allegedcrime_brundage']
    # Get the json object require for displaying timemap data    
    timemap = Timemap(filters)    
    jsonResult = timemap.get_json()

    return render(request, 'events/timemap.html', \
        {'data' : mark_safe(jsonResult), \
         'filters' : timemap.filterTags})

def json_data(request):
    '''
    Returns returns json data for map display
    '''

    map_data = Timemap()
    map_json = json.dumps(map_data.get_json(), indent=4)
    response = HttpResponse(map_json, mimetype='application/json')

    return response


