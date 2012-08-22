import json
from django.core.urlresolvers import reverse
from django.test import TestCase

class GraphViewTest(TestCase):
    fixtures = ['test_lynchings', 'test_reldata']

    def test_filters(self):
        response = self.client.get(reverse('relations:graph'))
        self.assertEqual(response.status_code, 200)

        filters = response.context['filters']
        self.assertEqual(len(filters), 1)

        action_filter = filters[0]
        self.assertEqual(action_filter['http_name'], 'action')
        self.assertTrue('label' in action_filter)

        values = action_filter['values']
        self.assertEqual(len(values), 4)

        self.assertEqual(values[0]['label'], 'All (6)')
        self.assertEqual(values[0]['value'], '')
        self.assertEqual(values[0]['count'], 6)

        self.assertEqual(values[1]['label'], 'violence against people (3)')
        self.assertEqual(values[1]['value'], 1)
        self.assertEqual(values[1]['count'], 3)

        self.assertEqual(values[2]['label'], 'threat (2)')
        self.assertEqual(values[2]['value'], 2)
        self.assertEqual(values[2]['count'], 2)

        self.assertEqual(values[3]['label'], 'surrender (1)')
        self.assertEqual(values[3]['value'], 3)
        self.assertEqual(values[3]['count'], 1)


class GraphDataViewTest(TestCase):
    fixtures = ['test_lynchings', 'test_reldata']

    def test_basic_structure(self):
        response = self.client.get(reverse('relations:graph_data'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        data = json.loads(response.content)
        self.assertTrue('nodes' in data)
        self.assertTrue('links' in data)

        self.assertTrue('name' in data['nodes'][0])
        self.assertTrue('value' in data['nodes'][0])
        self.assertTrue('actor_id' in data['nodes'][0])

        self.assertTrue('source' in data['links'][0])
        self.assertTrue('source_id' in data['links'][0])
        self.assertTrue('target' in data['links'][0])
        self.assertTrue('target_id' in data['links'][0])
        self.assertTrue('value' in data['links'][0])

    def test_unfiltered_data(self):
        response = self.client.get(reverse('relations:graph_data'))
        data = json.loads(response.content)

        self.assertEqual(len(data['nodes']), 3)
        # data not guaranteed to be sorted. sort them here for easy testing
        nodes = sorted(data['nodes'], key=lambda n:n['actor_id'])
        links = sorted(data['links'], key=lambda d:(d['source_id'], d['target_id']))

        self.assertEqual(len(nodes), 3)

        self.assertEqual(nodes[0]['actor_id'], 1)
        self.assertEqual(nodes[0]['name'], 'police')
        self.assertEqual(nodes[0]['value'], 2)

        self.assertEqual(nodes[1]['actor_id'], 2)
        self.assertEqual(nodes[1]['name'], 'citizens')
        self.assertEqual(nodes[1]['value'], 6)

        self.assertEqual(nodes[2]['actor_id'], 3)
        self.assertEqual(nodes[2]['name'], 'crowd')
        self.assertEqual(nodes[2]['value'], 4)

        self.assertEqual(len(links), 3)

        self.assertEqual(links[0]['source_id'], 1)
        self.assertEqual(links[0]['target_id'], 2)
        self.assertEqual(links[0]['value'], 2)
        # source/target point to an index in nodes. verify that node's
        # actor_id the same as the link's source/target id
        self.assertEqual(data['nodes'][links[0]['source']]['actor_id'], 1)
        self.assertEqual(data['nodes'][links[0]['target']]['actor_id'], 2)

        self.assertEqual(links[1]['source_id'], 2)
        self.assertEqual(links[1]['target_id'], 3)
        self.assertEqual(links[1]['value'], 2)
        self.assertEqual(data['nodes'][links[1]['source']]['actor_id'], 2)
        self.assertEqual(data['nodes'][links[1]['target']]['actor_id'], 3)

        self.assertEqual(links[2]['source_id'], 3)
        self.assertEqual(links[2]['target_id'], 2)
        self.assertEqual(links[2]['value'], 2)
        self.assertEqual(data['nodes'][links[2]['source']]['actor_id'], 3)
        self.assertEqual(data['nodes'][links[2]['target']]['actor_id'], 2)

    def test_filtered_data(self):
        response = self.client.get(reverse('relations:graph_data'), {'action': 1})
        data = json.loads(response.content)

        self.assertEqual(len(data['nodes']), 3)
        # data not guaranteed to be sorted. sort them here for easy testing
        nodes = sorted(data['nodes'], key=lambda n:n['actor_id'])
        links = sorted(data['links'], key=lambda d:(d['source_id'], d['target_id']))

        self.assertEqual(len(nodes), 3)

        self.assertEqual(nodes[0]['actor_id'], 1)
        self.assertEqual(nodes[0]['name'], 'police')
        self.assertEqual(nodes[0]['value'], 2)

        self.assertEqual(nodes[1]['actor_id'], 2)
        self.assertEqual(nodes[1]['name'], 'citizens')
        self.assertEqual(nodes[1]['value'], 3)

        self.assertEqual(nodes[2]['actor_id'], 3)
        self.assertEqual(nodes[2]['name'], 'crowd')
        self.assertEqual(nodes[2]['value'], 1)

        self.assertEqual(len(links), 2)

        self.assertEqual(links[0]['source_id'], 1)
        self.assertEqual(links[0]['target_id'], 2)
        self.assertEqual(links[0]['value'], 2)
        self.assertEqual(data['nodes'][links[0]['source']]['actor_id'], 1)
        self.assertEqual(data['nodes'][links[0]['target']]['actor_id'], 2)

        self.assertEqual(links[1]['source_id'], 3)
        self.assertEqual(links[1]['target_id'], 2)
        self.assertEqual(links[1]['value'], 1)
        self.assertEqual(data['nodes'][links[1]['source']]['actor_id'], 3)
        self.assertEqual(data['nodes'][links[1]['target']]['actor_id'], 2)


class EventViewTest(TestCase):
    fixtures = ['test_lynchings', 'test_reldata']

    def test_basic_structure(self):
        response = self.client.get(reverse('relations:event_lookup'), {'participant': 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        data = json.loads(response.content)

        self.assertTrue('url' in data[0])
        self.assertTrue('name' in data[0])
        self.assertTrue(data[0]['name'].startswith('Lynching of '))
        self.assertTrue('appearances' in data[0])

    def test_participant_only(self):
        response = self.client.get(reverse('relations:event_lookup'), {'participant': 3})
        data = json.loads(response.content)

        self.assertEqual(len(data), 3)

        self.assertEqual(data[0]['url'], reverse('lynchings:lynching_detail', args=[2]))
        self.assertEqual(data[0]['appearances'], 2)

        self.assertEqual(data[1]['url'], reverse('lynchings:lynching_detail', args=[1]))
        self.assertEqual(data[1]['appearances'], 1)

        self.assertEqual(data[2]['url'], reverse('lynchings:lynching_detail', args=[3]))
        self.assertEqual(data[2]['appearances'], 1)

    def test_filter_action(self):
        response = self.client.get(reverse('relations:event_lookup'),
                                   {'participant': 3, 'action': 2})
        data = json.loads(response.content)

        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['url'], reverse('lynchings:lynching_detail', args=[1]))
        self.assertEqual(data[0]['appearances'], 1)

        self.assertEqual(data[1]['url'], reverse('lynchings:lynching_detail', args=[3]))
        self.assertEqual(data[1]['appearances'], 1)
