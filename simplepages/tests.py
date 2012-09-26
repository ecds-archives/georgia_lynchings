from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.client import Client

from georgia_lynchings.simplepages.models import Page

class SimpleViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        test_pages = [
            {'title': 'Test 1', 'content': 'Test test test', 'slug': 'test-1' },
            {'title': 'Test 2', 'content': 'Test test test', 'slug': 'test-2' },
            {'title': 'Test 3', 'content': 'Test test test', 'slug': 'test-3' },
        ]
        for page_data in test_pages:
            page = Page(**page_data)
            page.save()

    def test_page_view(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        page_list = Page.objects.all()
        expected = 200
        for page in page_list:
            url = reverse('simplepages:view', args=[page.slug])
            actual = self.client.get(url).status_code
            self.failUnlessEqual(expected, actual,
                'Expected %s but returned %s for %s' % (expected, actual, url))
