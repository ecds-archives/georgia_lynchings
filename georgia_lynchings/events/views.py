import json
import logging
import sunburnt
from operator import __or__ as OR

from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.shortcuts import render

from georgia_lynchings import geo_coordinates
from georgia_lynchings.events.forms import SearchForm, AdvancedSearchForm
from georgia_lynchings.events.models import MacroEvent, Victim, SemanticTriplet
from georgia_lynchings.articles.models import Article

logger = logging.getLogger(__name__)

                        
def detail(request, row_id):
    """
    Renders a view for a specific macro event of row_id.

    :param row_id:  Id of the macroevent.

    """
    try:
        event = MacroEvent.objects.get(row_id)
    except ObjectDoesNotExist:
        raise Http404 # Raise 404 if no MacroEvent with that ID in the triplestore

    victim_names = None
    map_markers = []
    if event.victims:
        victim_names = [victim.primary_name for victim in event.victims]
        county_names = set([victim.primary_county for victim in event.victims])
        for county in county_names: # Used for map panel markers
            geo = geo_coordinates.countymap.get(county, None)
            if geo:
                map_markers.append({"county": county, "lat": geo['latitude'], "long": geo['longitude']})
        dates = sorted(set([victim.primary_lynching_date for victim in event.victims if victim.primary_lynching_date]))
        if len(dates) > 1:
            dates = [dates[0], dates[-1]]

    q_list = [Q(identifier=document.uri) for document in event.documents]
    articles = Article.objects.filter(reduce(OR, q_list))

    return render(request, 'events/details.html',{
        'event': event,
        'victim_names': victim_names,
        'county_names': county_names,
        'dates': sorted(dates),
        'articles': articles,
        'map_markers': map_markers,
    })

def home(request):
    return render(request, 'index.html')

def macro_events(request):
    '''List all macro events, provide article count.'''

    events = MacroEvent.objects.fields(
        'victims__name', 'victims__alt_name', 'victims__brundage__name',
        'victims__county_of_lynching', 'victims__brundage__county_of_lynching',
        'victims__date_of_lynching', 'victims__brundage__date_of_lynching',
        ).all()

    return render(request, 'events/list_events.html', {
        'events': events,
    })

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


def timemap(request):
    # TODO: filter info is heavily dependent on the data itself. move filter
    # generation either to the client js, or tie it somehow to timemap_data().
    return render(request, 'events/timemap.html')

def timemap_victim_data(request):
    victims = Victim.objects \
              .fields('name', 'alt_name', 'county_of_lynching',
                      'alleged_crime', 'date_of_lynching', 'brundage__name',
                      'brundage__county_of_lynching',
                      'brundage__alleged_crime',
                      'brundage__date_of_lynching', 'macro_event') \
              .all()
    victim_data = [_victim_timemap_data(v) for v in victims]
    json_literal = [d for d in victim_data
                    if d.get('start', None) and
                       d.get('point', None)]
    return HttpResponse(json.dumps(json_literal, indent=4),
                        mimetype='application/json')

def _victim_timemap_data(victim):
    data = {
        'title': victim.primary_name or 'Unnamed victim',
        'options': {
            'detail_link': victim.macro_event.get_absolute_url(),
        }
    }

    county = victim.primary_county
    if county:
        data['options']['county'] = county
        coords = geo_coordinates.countymap.get(county, None)
        if coords:
            data['point'] = {'lat': coords['latitude'],
                             'lon': coords['longitude']}
        else:
            logger.info('No county coordinages for %s county (victim %s)' % (county, victim.id))
    
    crime = victim.primary_alleged_crime
    if crime:
        data['options']['alleged_crime'] = crime

    date = victim.primary_lynching_date
    if date:
        # strftime can't reliably do dates before 1900
        date_str = "%s-%s-%s" % (date.year, date.month, date.day)
        data['start'] = date_str
        data['options']['date'] = date_str

    return data
