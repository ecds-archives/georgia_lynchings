from collections import defaultdict, OrderedDict
import json

from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from georgia_lynchings.lynchings.models import Story, Lynching
from georgia_lynchings.reldata import models

FILTER_FIELDS = [
    {
        'field_label': 'Type of Interaction',
        'http_name': 'action',
        'value_field': 'action',
        'label_field': 'action__description',
    },
]

def graph(request):
    '''Display a force-directed graph showing relationships between types of
    people.
    '''

    rel_qs = models.Relation.objects.filter(subject__isnull=False,
                                            action__isnull=False,
                                            object__isnull=False)

    filters = []
    for field in FILTER_FIELDS:
        value_data = rel_qs.values(field['value_field'], field['label_field'])\
                           .annotate(Count('id'))
        raw_values = [{
            'label': '%s (%d)' % (v[field['label_field']],
                                  v['id__count']),
            'value': v[field['value_field']],
            'count': v['id__count'],
        } for v in value_data]
        all_rels = {
            'label': 'All (%d)' % (len(rel_qs),),
            'value': '',
            'count': len(rel_qs),
        }
        values = sorted([all_rels] + raw_values, key=lambda v:v['count'], reverse=True)
        filter = {
            'label': field['field_label'],
            'http_name': field['http_name'],
            'values': values,
        }
        filters.append(filter)

    return render(request, 'reldata/graph.html', {
            'data_url': reverse('relations:graph_data'),
            'event_url': reverse('relations:event_lookup'),
            'filters': filters,
        })

def wordcloud(request):
    rels = models.Relation.objects.exclude(subject_adjective="").\
    values('subject_adjective').annotate(Count('subject_adjective'))
    word_list = [{'word': rel['subject_adjective'], 'count': rel['subject_adjective__count']}
    for rel in rels]

    return render(request, 'reldata/wordle.html', {
        'word_list': word_list,
    })

def filtered_relation_query(request):
    '''Get a query set representing :class:`~georgia_lynchings.reldata.models.Relation`
    objects after applying common filter arguments in the request.
    '''
    rel_qs = models.Relation.objects.filter(subject__isnull=False,
                                            action__isnull=False,
                                            object__isnull=False)
    for field in FILTER_FIELDS:
        value = request.GET.get(field['http_name'], '')
        if value:
            rel_qs = rel_qs.filter(**{field['value_field']: value})
    return rel_qs

def graph_data(request):
    '''Collect data for a (force-directed) relationship graph from available
    :class:`~georgia_lynchings.reldata.models.Relation` data.
    '''
    rel_qs = filtered_relation_query(request)
    subjects = rel_qs.values('subject').annotate(Count('id'))
    subjects_dict = {subj['subject']: subj['id__count'] for subj in subjects}
    objects = rel_qs.values('object').annotate(Count('id'))
    objects_dict = {obj['object']: obj['id__count'] for obj in objects}

    actors = models.Actor.objects.order_by('id')
    raw_nodes = [{
        'name': actor.description,
        'value': subjects_dict.get(actor.id, 0) + \
                 objects_dict.get(actor.id, 0),
        'actor_id': actor.id,
    } for actor in actors]
    nodes = [n for n in raw_nodes if n['value']]
    node_dict = {n['actor_id']: (n, i) for i, n in enumerate(nodes)}

    pairs = rel_qs.values('subject', 'object').annotate(Count('id'))
    links = [{
        'source': node_dict[pair['subject']][1],
        'source_id': node_dict[pair['subject']][0]['actor_id'],
        'target': node_dict[pair['object']][1],
        'target_id': node_dict[pair['object']][0]['actor_id'],
        'value': pair['id__count'],
    } for pair in pairs.order_by('subject', 'object')]

    result = {
        'nodes': nodes,
        'links': links,
    }
    result_s = json.dumps(result)
    return HttpResponse(result_s, content_type='application/json')


def cloud_data(request):
    '''
    Generates json data for the wordcloud view.
    '''
    rels = models.Relation.objects.exclude(subject_adjective="").\
        values('subject_adjective').annotate(Count('subject_adjective'))
    data = [{'word': rel['subject_adjective'], 'count': rel['subject_adjective__count']}
        for rel in rels]
    return HttpResponse(json.dumps(data), content_type='application/json')


def event_lookup(request):
    '''Look up lynching stories and instance counts for relations matching
    query terms.
    '''
    if 'participant' not in request.GET:
        msg = "Event search requires search terms. Current recognized " + \
              "search terms are: participant"
        return HttpResponseBadRequest(msg)
    participant = int(request.GET.get('participant'))

    qs = filtered_relation_query(request)
    qs = qs.filter(Q(subject=participant) |
                   Q(object=participant))
    rel_data = qs.values('story_id') \
                 .annotate(Count('id'))

    lynching_data = []
    for rel in rel_data:
        try:
            lynching = Lynching.objects.get(id=rel['story_id'])
            lynching_data.append({
                'url': reverse('lynchings:lynching_detail', args=[lynching.id,]),
                'name': "%s" % lynching, # Use the string method.
                'appearances': rel['id__count'],
                })
        except Lynching.DoesNotExist:
            pass
    sorted_data = sorted(lynching_data, key=lambda s:s['appearances'], reverse=True)
    return HttpResponse(json.dumps(sorted_data),
                        content_type='application/json')
