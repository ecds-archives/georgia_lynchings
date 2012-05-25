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
            return self.nodes[name]
        else:
            num = len(self.nodes)
            self.nodes[name] = num
            return num


def graph_data(request):
    rels = RelationsCollection()
    for rel in Relationship.objects.all():
        rels.add_relationship_object(rel)

    result = {
        'nodes': [{'name':key} for key in rels.nodes],
        'links': [{'source':key[0], 'target':key[1], 'value':val}
                  for (key, val) in rels.links.iteritems()],
    }
    result_s = json.dumps(result)
    return HttpResponse(result_s, content_type='application/json')

