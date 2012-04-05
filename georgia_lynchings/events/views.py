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
from django.template.defaultfilters import slugify
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
]

def timemap(request):
    '''Send list of filters generated from :class:`~georgia_lynchings.events.timemap.Timemap`
    to the template for the filter dropdown lists.
    '''
    # FIXME: the frequencies should be calcuated as the timemap is built for accuracy.
    return render(request, 'events/timemap.html', \
        {'filters' : get_filters(filters)})

# FIXME: rename this method once refactoring is complete and its purpose
# becomes clearer. probably change the url as well.
def map_json(request):
    macro_events = _get_macro_events_for_timemap()
    macro_data = [ _macro_event_timemap_data(me) for me in macro_events ]
    # FIXME: several events have no start or end date associated with them.
    # ideally, we should find a way to associate dates with these items.
    # lacking that, we should consider how we can include them in the data
    # set, since right now they're entirely invisible in the timemap.
    json_literal = [d for d in macro_data
                    if d.get('start', None) and
                       d.get('end', None) and
                       d.get('point', None)]
    return HttpResponse(json.dumps(json_literal, indent=4),
                        mimetype='application/json')

def _get_macro_events_for_timemap():
    return MacroEvent.objects \
           .fields('label', 'events__start_date', 'events__end_date', 
                   'victims__victim_county_of_lynching',
                   'victims__victim_alleged_crime') \
           .all()
# FIXME: or even better, the properties actually used in this view so that
# the view doesn't need to know model implementation details:
#    return MacroEvent.objects \
#        .fields('label', '_tmp_start', '_tmp_end', '_tmp_coords',
#                '_tmp_cities', '_tmp_county', '_tmp_alleged_crimes') \
#        .all()

def _macro_event_timemap_data(mac):
    '''Get the timemap json data for a single
    :class:`~georgia_lynchings.events.models.MacroEvent`.'''
    # TODO: revisit json actually needed by timemap

    # base data available (we think) for all macro events:
    data = {
        'title': mac.label,
        'options': {
            'county': mac._tmp_county(),
            'detail_link': mac.get_absolute_url(),
            'min_date': mac._tmp_start(),
            'tags': _macro_event_tags(mac),
            'title': mac.label,
            'victim_allegedcrime_brundage_filter': mac._tmp_alleged_crimes(),
        },
    }

    # add fields that might not actually be available for some macro events:

    start_date = mac._tmp_start()
    if start_date:
        data['start'] = start_date

    end_date = mac._tmp_end()
    if end_date:
        data['end'] = end_date

    coords = mac._tmp_coords()
    if coords:
        data['point'] = { 'lat':coords['latitude'],
                          'lon':coords['longitude']}

    return data
    
def _macro_event_tags(mac):
    'Get the timemap tags used for filtering a macro event.'
    # TODO: revisit filtering

    alleged_crimes = mac._tmp_alleged_crimes()
    alleged_crime_tags = [slugify('ac ' + c) for c in alleged_crimes]

    return alleged_crime_tags
