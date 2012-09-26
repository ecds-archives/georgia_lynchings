import json

from django.http import Http404, HttpResponse
from django.db.models import Count, Q, Sum, Avg
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse

from georgia_lynchings.lynchings.models import Story, Lynching, Accusation, Victim
from georgia_lynchings.demographics.models import County, Population
from georgia_lynchings.reldata.models import Relation

def index(request):
    """
    A Basic index view for the front page of the site.
    """
    count  = {
        'lynching': Lynching.objects.all().count,
        'victim': Victim.objects.all().count,
        'county': County.objects.filter(victim__isnull=False).count,
        'accusation': Accusation.objects.all().count,
        'relation': Relation.objects.all().count,
        }
    return render(request, 'index.html', {
            'count': count,
        })

def lynching_detail(request, lynching_id):
    """
    Renders a detailed view for a specific story_id.
    """
    lynching = get_object_or_404(Lynching, pk=lynching_id)

    population_list, closest_census, state_averages = None, None, None
    if lynching.year:
        closest_census = (lynching.year/10)*10 # parens un-needed but can't help myself.
        if lynching.year%10 > 5 and lynching.year < 1930:
            closest_census = closest_census + 10

        population_list = Population.objects.filter(county__in=lynching.county_list, year=closest_census)
        state_averages = Population.objects.filter(year=closest_census).aggregate(
            total=Sum('total'),
            white=Sum('white'),
            black=Sum('black'),
            ilterate_blacks=Sum('iltr_black'),
            iliterate_whites=Sum('iltr_white'),
            county_avg_total=Sum('total'),
            county_avg_white=Sum('white'),
            county_avg_black=Sum('black'),
            county_avg_ilterate_blacks=Sum('iltr_black'),
            county_avg_iliterate_whites=Sum('iltr_white'),
        )

    return render(request, 'lynchings/details.html',{
        'lynching': lynching,
        'population_list': population_list,
        'state_averages': state_averages,
        'census_year': closest_census,
        })

def lynching_list(request):
    """
    Renders a simple list of lynching stories.
    """
    lynching_list = Lynching.objects.all()

    return render(request, 'lynchings/list_events.html', {
        'lynching_list': lynching_list,
        'title': "All Lynchings",
    })

def lynching_list_by_accusation(request, accusation_id):
    """
    Returns a list of lynchings based on the accusations that lead to the event.
    """
    crime = get_object_or_404(Accusation, id=accusation_id)
    lynching_list = Lynching.objects.filter(victim__accusation=crime).distinct()

    return render(request, 'lynchings/list_events.html', {
        'lynching_list': lynching_list,
        'title': "Lynchings After an Accusation of %s" % crime.label,
    })

def alleged_crimes_list(request):
    """
    Returns a list of alleged crimes with counts for number of related lynhcings.
    """
    accusation_list = Accusation.objects.exclude(victim__isnull=True).annotate(victim_count=Count('victim__pk'))
    # hacky way to render multiple columns.
    try:
        slice_at = len(accusation_list)/2
    except ValueError:
        slice_at = 0
    return render(request, 'lynchings/alleged_crimes.html', {
        'accusation_list': accusation_list,
        'slice_at': slice_at,
    })

def county_list(request):
    """
    Returns a list of counties.
    """
    county_list = County.objects.exclude(victim__isnull=True).annotate(victim_count=Count('victim__pk'))

    return render(request, 'lynchings/county_list.html', {
        'title': "Georgia Counties with recorded Lynchings",
        'counties_list': county_list,
    })

def county_detail(request, county_id):
    """
    Returns a particular county.
    """
    county = get_object_or_404(County, id=county_id)

    lynching_list = Lynching.objects.filter(victim__county=county).distinct()
    return render(request, 'lynchings/list_events.html', {
        'title': 'Lynchings in %s County' % county.name,
        'county': county,
        'lynching_list': lynching_list,
    })

def timemap(request):
    return render(request, 'lynchings/timemap.html')

def timemap_data(request):
    """
    Renders a json return for use with timemap.
    """
    story_data = [_story_timemap_data(lynching) for lynching in Lynching.objects.all()]
    json_literal = [d for d in story_data
                    if d.get('start', None) and
                       d.get('point', None)]

    return HttpResponse(json.dumps(json_literal, indent=4),
        mimetype='application/json')

def _story_timemap_data(lynching):
    """
    Formats a datapoint for an individual lynching story.

    """
    data = {
        'title': u'%s' % lynching,
        'options': {
            'detail_link': reverse('lynchings:lynching_detail', args=[lynching.id,]),
            }
    }
    try:
        county = lynching.county_list[0]
        if county:
            data['options']['county'] = county.name
            data['point'] = {
                'lat': county.latitude,
                'lon': county.longitude,
            }
    except IndexError:
        pass

    try:
        accusations = []
        for victim in [victim for victim in lynching.victim_set.all() if victim.accusation]:
            accusations.extend(victim.accusation.all())
        data['options']['alleged_crime'] = accusations[0].label # all crimes are the same or none.
    except IndexError:
        pass

    try:
        date = [victim.date for victim in lynching.victim_set.all() if victim.date][0]
        # strftime can't reliably do dates before 1900
        date_str = "%04d-%02d-%02d" % (date.year, date.month, date.day)
        data['start'] = date_str
        data['options']['date'] = date_str
    except IndexError:
        pass

    return data
