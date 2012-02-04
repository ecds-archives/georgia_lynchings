import json
import logging
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from pprint import pprint
from django.utils import simplejson
import sunburnt
from urllib import quote
import urllib2
from georgia_lynchings.forms import SearchForm
from georgia_lynchings.events.models import MacroEvent, \
        get_events_by_locations, get_events_by_times, get_all_macro_events, \
        SemanticTriplet
from georgia_lynchings.forms import SearchForm        

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
                result['docpath_link'] = quote(result['docpath'].replace('\\', '/'))
                result['docpath'] = result['docpath'][10:] 
    else:   title = "No records found" 
    # set prev/next links
    pagelink = {}    
    pagelink['prev']='../../%s/articles' % (int(row_id) - 1)
    pagelink['next']='../../%s/articles' % (int(row_id) + 1)    
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
    pagelink['prev']='../../%s/details' % (int(row_id) - 1)
    pagelink['next']='../../%s/details' % (int(row_id) + 1)    
    if results:   
        title = row_id
        results['articles_link'] = '../../../events/%s/articles' % row_id
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


def timemap(request):
    """
    Send external json file data to the timemap template.
    """
    
    # Check to make sure the TIMEMAP_JSON_URL is defined in the settings file.
    if not hasattr(settings, 'TIMEMAP_JSON_URL') or not settings.TIMEMAP_JSON_URL:
        logger.error('TIMEMAP_JSON_URL setting is not defined.')
        # TODO: review error handling
        raise Http404        
    else:    
        timemap_data = get_timemap_info()
        #print timemap_data
        return render(request, 'events/timemap.html', {'data' : mark_safe(timemap_data)})  


def get_timemap_info():
    '''
    Function to query all macro evnts and retun map data
    in json format
    
    :rtype: a serialized obj as a JSON formatted stream  

    This is an example of the json properties:
    timemap_data = [
        {
            "id": "event",
            "title": "Events",
            "theme": "red",
            "type": "basic",
            "options": {
                "items": [
                    {
                      "title" : "Columbia",
                      "start" : "1875-01-01",
                      "end" : "1875-01-14",                      
                      "point" : {
                          "lat" : 31.753389,
                          "lon" : -82.28558
                       },
                      "options" : {
                        "infoHtml": "<div><b>Columbia</b></div>" +
                                    "<div>Start date: 1875-01-01</div>" +
                                    "<div>End date: 1875-01-14</div>" +
                                    "<div>Location: Bibb County</div>" +
                                    "<div>Victims: John and Jane Doe</div>" +
                                    "<div><a target='_blank' href='../../../events/100/details'>more info</a></div>"
                      }
                    }
                ]
            }
        }
    ]
    '''
    
    # Request the TIMEMAP_JSON_URL property in settings
    try:
        req = urllib2.Request(settings.TIMEMAP_JSON_URL)
        opener = urllib2.build_opener()
        jsondata = opener.open(req)
        # return the serialized obj as a JSON formatted stream        
        return json.dumps(simplejson.load(jsondata))
    except:
        # TODO: review error handling
        raise Http404
