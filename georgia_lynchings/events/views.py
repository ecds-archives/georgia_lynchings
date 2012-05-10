import json
import logging
from operator import __or__ as OR

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.shortcuts import render

from georgia_lynchings import geo_coordinates
from georgia_lynchings.events.models import MacroEvent, Victim
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
        date_str = "%04d-%02d-%02d" % (date.year, date.month, date.day)
        data['start'] = date_str
        data['options']['date'] = date_str

    return data
