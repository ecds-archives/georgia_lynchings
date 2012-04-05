import json
import logging
from pprint import pprint
import sunburnt
from urllib import quote
import urllib2

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe

from georgia_lynchings.events.details import Details   
from georgia_lynchings.events.forms import SearchForm, AdvancedSearchForm
from georgia_lynchings.events.models import MacroEvent, \
    get_all_macro_events, SemanticTriplet, get_filters
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
    # FIXME: The details module is deprecated. Pass the MacroEvent model
    # directly to the template and let it grab the information it needs.
    details = Details(row_id)
    results = details.get()

    #Article data
    event = MacroEvent(row_id)
    article_data = event.get_articles()

    if results:
        title = row_id
        results['articles_link'] = reverse('events:articles', kwargs={'row_id': row_id})          
    else:   title = "No records found"  
     
    return render(request, 'events/details.html',
                  {'results': results, 'row_id':row_id, 'title':title, 'article_data':article_data})

    
def home(request):
    template = 'index.html'
    return render(request, template, {'search_form': SearchForm()})

def macro_events(request):
    '''List all macro events, provide article count.'''

    # FIXME: get_all_macro_events() is deprecated. we need code in this
    # module to grab MacroEvent.objects.all() with any .fields() we want to
    # prepopulate.
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


def advanced_search(request):
    results = None
    form = AdvancedSearchForm(request.GET)
    form_fields = set(form.fields.keys())
    request_fields = set(k for (k, v) in request.GET.items() if v)
    # if the form is valid and at least one field is specified:
    if form.is_valid() and form_fields.intersection(request_fields):
        q = solr = sunburnt.SolrInterface(settings.SOLR_INDEX_URL)
        if form.cleaned_data['participant']:
            q = q.query(participant_name=form.cleaned_data['participant'])
        if form.cleaned_data['victims']:
            q = q.query(victim_name_brundage=form.cleaned_data['victims'])
        if form.cleaned_data['locations']:
            q = q.query(location=form.cleaned_data['locations'])
        if form.cleaned_data['alleged_crime']:
            q = q.query(victim_allegedcrime_brundage=form.cleaned_data['alleged_crime'])
        if form.cleaned_data['all_text']:
            q = q.query(text=form.cleaned_data['all_text'])
        q = q.filter(complex_type=MacroEvent.rdf_type)
        results = q.execute()

    return render(request, 'events/advanced_search.html',
                  {'form': form, 'results': results})


#These views and variables are for Map display

# Create filters for timemap
filters= [
    { 
        'title': 'Alleged Crime',
        'name': 'victim_allegedcrime_brundage',
        'prefix': 'ac',
        'dropdown_id': 'ac_tag_select',        
        # example of tag tuple (display name, slug, frequency):
        # 'tags': [
        #   ('Argument', 'ac_argument', 4), 
        #   ('Debt Dispute', 'ac_debt_dispute', 7), 
        #   ('Kidnapping/Theft', 'ac_kidnapping/theft', 17)
        # ]        
    },
    { 
        'title': 'Cities',
        'name': 'city',
        'prefix': 'city',
        'dropdown_id': 'city_tag_select',               
    }    
]

def timemap(request):
    '''Send list of filters generated from :class:`~georgia_lynchings.events.timemap.Timemap`
    to the template for the filter dropdown lists.
    '''
    # FIXME: the frequencies should be calcuated as the timemap is built for accuracy.
    return render(request, 'events/timemap.html', \
        {'filters' : get_filters(filters)})

def map_json(request):
    '''
    Renders json data from :class:`~georgia_lynchings.events.timemap.Timemap` for map display
    '''

    map_data = Timemap(filters)
    add_fields = get_additional_fields()
    # Get the json for core metadata plus any additional fields for the timemap filter
    json_str = json.dumps(map_data.get_json(add_fields=add_fields), indent=4)    
    response = HttpResponse(json_str, mimetype='application/json')

    return response
    
def get_additional_fields():
    '''
    Create a list of names for the timemap filter fields.
    
    :rtype: a list of filter names    
    '''    
        
    # Get a list of filter names
    fields = []
    for filter in filters:
        fields.append(filter['name'])
    return fields    
