from collections import defaultdict, OrderedDict
import json

from django.http import HttpResponse
from georgia_lynchings.reldata.models import Relationship

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
        self.links[(subj_node, obj_node)] += 1

    def get_node(self, name):
        if name in self.nodes:
            val = self.nodes[name]
            val['count'] += 1
        else:
            num = len(self.nodes)
            val = {'num': num, 'count': 1}
            self.nodes[name] = val
        return val['num']


def graph_data(request):
    rels = RelationsCollection()
    for rel in Relationship.objects.all():
        rels.add_relationship_object(rel)

    result = {
        'nodes': [{'name': name,
                   'weight': node['count']}
                  for name, node in rels.nodes.iteritems()],
        'links': [{'source': key[0],
                   'target': key[1],
                   'value': val}
                  for (key, val) in rels.links.iteritems()],
    }
    result_s = json.dumps(result)
    return HttpResponse(result_s, content_type='application/json')

