import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

class GraphViewTest(TestCase):
    fixtures = ['test_relations']

    graph_url = reverse('relations:graph')
    data_url = reverse('relations:graph_data')

    def setUp(self):
        self.client = Client()

    def test_render(self):
        resp = self.client.get(self.graph_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['data_url'], self.data_url)

    def test_filters(self):
        resp = self.client.get(self.graph_url)
        filters = resp.context['filters']
        self.assertTrue(('subject gender', 'subject_gender',
                         ['', 'female', 'male'])
                        in filters)
        self.assertTrue(('object gender', 'object_gender',
                         ['', 'female', 'male'])
                        in filters)
        self.assertTrue(('subject race', 'subject_race',
                         ['', 'negro', 'white'])
                        in filters)
        self.assertTrue(('object race', 'object_race',
                         ['', 'colored', 'negro', 'white'])
                        in filters)


class GraphDataViewTest(TestCase):
    fixtures = ['test_relations']

    data_url = reverse('relations:graph_data')

    def setUp(self):
        self.client = Client()

    def test_json_data(self):
        resp = self.client.get(self.data_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/json')
        obj = json.loads(resp.content)

    def test_nodes(self):
        resp = self.client.get(self.data_url)
        obj = json.loads(resp.content)
        self.assertTrue('nodes' in obj)
        self.assertEqual(len(obj['nodes']), 8)

        # dict mapping name -> node for easier lookup
        nodes_by_names = dict((node['name'], node)
                              for node in obj['nodes'])
        self.assertEqual(nodes_by_names['marshal']['weight'], 2)
        self.assertEqual(nodes_by_names['colored']['weight'], 3)
        self.assertEqual(nodes_by_names['mayor']['weight'], 1)
        self.assertEqual(nodes_by_names['sheriff']['weight'], 3)
        self.assertEqual(nodes_by_names['mother']['weight'], 2)
        self.assertEqual(nodes_by_names['deputy']['weight'], 1)
        self.assertEqual(nodes_by_names['policeman']['weight'], 1)
        self.assertEqual(nodes_by_names['burglar']['weight'], 1)

    def test_links(self):
        resp = self.client.get(self.data_url)
        obj = json.loads(resp.content)
        self.assertTrue('links' in obj)
        self.assertEqual(len(obj['links']), 6)

        # dict mapping (source, target) -> link for easier lookup
        links_by_names = dict(((link['source_name'], link['target_name']), link)
                              for link in obj['links'])
        self.assertEqual(links_by_names[('marshal', 'colored')]['value'], 2)
        self.assertEqual(links_by_names[('mayor', 'sheriff')]['value'], 1)
        self.assertEqual(links_by_names[('sheriff', 'mother')]['value'], 1)
        self.assertEqual(links_by_names[('sheriff', 'deputy')]['value'], 1)
        self.assertEqual(links_by_names[('colored', 'policeman')]['value'], 1)
        self.assertEqual(links_by_names[('mother', 'burglar')]['value'], 1)

    def test_subject_gender_filter(self):
        resp = self.client.get(self.data_url + '?subject_gender=female')
        obj = json.loads(resp.content)

        self.assertEqual(len(obj['nodes']), 2)
        nodes_by_names = dict((node['name'], node)
                              for node in obj['nodes'])
        self.assertEqual(nodes_by_names['mother']['weight'], 1)
        self.assertTrue('marshal' not in nodes_by_names)

        self.assertEqual(len(obj['links']), 1)
        links_by_names = dict(((link['source_name'], link['target_name']), link)
                              for link in obj['links'])
        self.assertEqual(links_by_names[('mother', 'burglar')]['value'], 1)
        self.assertTrue(('marshal', 'colored') not in links_by_names)

    def test_object_gender_filter(self):
        resp = self.client.get(self.data_url + '?object_gender=female')
        obj = json.loads(resp.content)

        self.assertEqual(len(obj['nodes']), 2)
        nodes_by_names = dict((node['name'], node)
                              for node in obj['nodes'])
        self.assertEqual(nodes_by_names['sheriff']['weight'], 1)
        self.assertTrue('marshal' not in nodes_by_names)

        self.assertEqual(len(obj['links']), 1)
        links_by_names = dict(((link['source_name'], link['target_name']), link)
                              for link in obj['links'])
        self.assertEqual(links_by_names[('sheriff', 'mother')]['value'], 1)
        self.assertTrue(('marshal', 'colored') not in links_by_names)

    def test_subject_race_filter(self):
        resp = self.client.get(self.data_url + '?subject_race=white')
        obj = json.loads(resp.content)

        self.assertEqual(len(obj['nodes']), 2)
        nodes_by_names = dict((node['name'], node)
                              for node in obj['nodes'])
        self.assertEqual(nodes_by_names['policeman']['weight'], 1)
        self.assertTrue('marshal' not in nodes_by_names)

        self.assertEqual(len(obj['links']), 1)
        links_by_names = dict(((link['source_name'], link['target_name']), link)
                              for link in obj['links'])
        self.assertEqual(links_by_names[('policeman', 'colored')]['value'], 1)
        self.assertTrue(('marshal', 'colored') not in links_by_names)

    def test_object_race_filter(self):
        resp = self.client.get(self.data_url + '?object_race=white')
        obj = json.loads(resp.content)

        self.assertEqual(len(obj['nodes']), 2)
        nodes_by_names = dict((node['name'], node)
                              for node in obj['nodes'])
        self.assertEqual(nodes_by_names['deputy']['weight'], 1)
        self.assertTrue('marshal' not in nodes_by_names)

        self.assertEqual(len(obj['links']), 1)
        links_by_names = dict(((link['source_name'], link['target_name']), link)
                              for link in obj['links'])
        self.assertEqual(links_by_names[('sheriff', 'deputy')]['value'], 1)
        self.assertTrue(('marshal', 'colored') not in links_by_names)

    def test_combine_filters(self):
        resp = self.client.get(self.data_url + '?object_gender=male&object_race=white')
        obj = json.loads(resp.content)
        
        self.assertEqual(len(obj['nodes']), 2)
        nodes_by_names = dict((node['name'], node)
                              for node in obj['nodes'])
        self.assertEqual(nodes_by_names['deputy']['weight'], 1)
        self.assertTrue('mother' not in nodes_by_names)

        self.assertEqual(len(obj['links']), 1)
        links_by_names = dict(((link['source_name'], link['target_name']), link)
                              for link in obj['links'])
        self.assertEqual(links_by_names[('sheriff', 'deputy')]['value'], 1)
        self.assertTrue(('sheriff', 'mother') not in links_by_names)
