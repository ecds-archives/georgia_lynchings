import json

from django.http import Http404, HttpResponse
from django.db.models import Count, Q, Sum, Avg
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse

from georgia_lynchings.lynchings.models import Story, Person, Lynching, Accusation
from georgia_lynchings.demographics.models import County, Population

def story_detail(request, story_id):
    """
    Renders a detailed view for a specific story_id.
    """
    story = get_object_or_404(Story, pk=story_id)

    population_list, closest_census, state_averages = None, None, None
    if story.year:
        closest_census = (story.year/10)*10 # parens un-needed but can't help myself.
        if story.year%10 > 5 and story.year < 1930:
            closest_census = closest_census + 10

        population_list = Population.objects.filter(county__in=story.county_list, year=closest_census)
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
        'story': story,
        'population_list': population_list,
        'state_averages': state_averages,
        'census_year': closest_census,
        })

def story_list(request):
    """
    Renders a simple list of lynching stories.
    """
    story_list = Story.objects.all()

    return render(request, 'lynchings/list_events.html', {
        'story_list': story_list,
        'title': "All Lynchings",
    })

def story_list_by_accusation(request, accusation_id):
    """
    Returns a list of lynchings based on the accusations that lead to the event.
    """
    crime = get_object_or_404(Accusation, id=accusation_id)
    story_list = Story.objects.filter(lynching__alleged_crime=crime).distinct()

    return render(request, 'lynchings/list_events.html', {
        'story_list': story_list,
        'title': "Lynchings After an Accusation of %s" % crime.label,
    })

def alleged_crimes_list(request):
    """
    Returns a list of alleged crimes with counts for number of related lynhcings.
    """
    accusation_list = Accusation.objects.exclude(lynching__isnull=True).annotate(stories=Count('lynching__pk'))

    return render(request, 'lynchings/alleged_crimes.html', {
        'accusation_list': accusation_list,
    })

def county_list(request):
    """
    Returns a list of counties.
    """
    counties = County.objects.all() #.annotate(lynching_count=Count('lynching__story'), alt_count=Count('alternate_counties__story'))
    counties_list = []
    for county in counties: # Multiple field referces makes annotation unlikely, hacking a join.
        tpl = ( county,
                Story.objects.filter(
                    Q(lynching__county=county) | Q(lynching__alternate_counties=county)
                ).distinct().count()
        )
        counties_list.append(tpl)

    return render(request, 'lynchings/county_list.html', {
        'title': "List of all Georgia Counties",
        'counties_list': counties_list,
    })

def county_detail(request, county_id):
    """
    Returns a particular county.
    """
    county = get_object_or_404(County, id=county_id)

    story_list = Story.objects.filter(
        Q(lynching__county=county) | Q(lynching__alternate_counties=county)
    ).distinct()

    return render(request, 'lynchings/list_events.html', {
        'title': 'Lynchings in %s County' % county.name,
        'county': county,
        'story_list': story_list,
    })

def timemap(request):
    return render(request, 'lynchings/timemap.html')

def timemap_data(request):
    """
    Renders a json return for use with timemap.
    """
    story_data = [_story_timemap_data(story) for story in Story.objects.all()]
    json_literal = [d for d in story_data
                    if d.get('start', None) and
                       d.get('point', None)]

    return HttpResponse(json.dumps(json_literal, indent=4),
        mimetype='application/json')

def _story_timemap_data(story):
    """
    Formats a datapoint for an individual lynching story.

    """
    data = {
        'title': u'%s' % story,
        'options': {
            'detail_link': reverse('lynchings:story_detail', args=[story.id,]),
            }
    }
    try:
        county = story.county_list[0]
        if county:
            data['options']['county'] = county.name
            data['point'] = {
                'lat': county.latitude,
                'lon': county.longitude,
            }
    except IndexError:
        pass

    try:
        accusations = [lynching.alleged_crime.label for lynching in story.lynching_set.all()
                if lynching.alleged_crime]
        data['options']['alleged_crime'] = accusations[0] # all crimes are the same or none.
    except IndexError:
        pass

    try:
        date = [lynching.date for lynching in story.lynching_set.all() if lynching.date][0]
        # strftime can't reliably do dates before 1900
        date_str = "%04d-%02d-%02d" % (date.year, date.month, date.day)
        data['start'] = date_str
        data['options']['date'] = date_str
    except IndexError:
        pass

    return data
