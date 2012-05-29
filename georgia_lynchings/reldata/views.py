from collections import defaultdict, OrderedDict
import json

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render

from georgia_lynchings.reldata.models import Relationship
from georgia_lynchings.events.models import SemanticTriplet

def graph(request):
    data_urls = {
        'triples': reverse('relations:graph_triple_data'),
    }
    data_name = request.GET.get('source', None)
    data_url = data_urls.get(data_name, reverse('relations:graph_data'))
    return render(request, 'reldata/graph.html', {'data_url': data_url})


class RelationsCollection(object):
    def __init__(self):
        self.nodes = OrderedDict()
        self.links = defaultdict(int)

    def add_relationship_object(self, rel):
        if rel.subject_desc and rel.object_desc:
            self.add_single_relationship(rel.subject_desc, rel.object_desc)

    def add_single_relationship(self, subj, obj):
        subj_node = self.get_node(subj)
        obj_node = self.get_node(obj)

        # we're treating links as undirected for now. order them so that
        # (a, b) and (b, a) are counted together.
        if subj_node < obj_node:
            endpoints = (subj_node, obj_node)
        else:
            endpoints = (obj_node, subj_node)

        self.links[endpoints] += 1

    def get_node(self, name):
        if name in self.nodes:
            val = self.nodes[name]
            val['count'] += 1
        else:
            num = len(self.nodes)
            val = {'num': num, 'count': 1}
            self.nodes[name] = val
        return val['num']

    def as_graph_data(self):
        return {
            'nodes': [{'name': name,
                       'weight': node['count']}
                      for name, node in self.nodes.iteritems()],
            'links': [{'source': key[0],
                       'target': key[1],
                       'value': val}
                      for (key, val) in self.links.iteritems()],
        }
        


def graph_data(request):
    rels = RelationsCollection()
    for rel in Relationship.objects.all():
        rels.add_relationship_object(rel)

    result = rels.as_graph_data()
    result_s = json.dumps(result)
    return HttpResponse(result_s, content_type='application/json')


def graph_triple_data(request):
    rels = RelationsCollection()
    for subj, obj in triple_subject_object_pairs():
        if subj.actor_name and obj.actor_name:
            rels.add_single_relationship(subj.actor_name, obj.actor_name)

    result = rels.as_graph_data()
    result_s = json.dumps(result)
    return HttpResponse(result_s, content_type='application/json')


def triple_subject_object_pairs():
    FIELDS = [
        'participant_s__individuals__actor_name',
        'participant_o__individuals__actor_name',
        ]
    triplets = SemanticTriplet.objects.fields(*FIELDS).all()
    for tr in triplets:
        for ps in tr.participant_s:
            for po in tr.participant_o:
                for s in ps.individuals:
                    for o in po.individuals:
                        yield (s, o)
