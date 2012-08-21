from django.core.urlresolvers import reverse
from django.core.files import File
from django.test import TestCase
from django.test.client import Client

from georgia_lynchings.articles.models import Article, IMG_SIZE

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class ArticleTest(TestCase):
	"""
	Tests for the Article models methods.
	"""

	def setUp(self):
		test_file = os.path.normpath(os.path.join(BASE_DIR, "fixtures/testfile.pdf"))
		data = {
			'file': File(open(test_file, 'rb')),
			'title': "This is a test file",
		}
		self.article = Article(**data)
		self.article.save()

	def tearDown(self):
		self.article.file.delete()

	def test_generate_thumbnail(self):
		expected = 'Generated Image: testfile_med.png'
		actual = self.article.generate_thumbnail(dryrun=True)
		self.assertEqual(expected, actual)

	def test_generate_all_thumbnails(self):
		extension_list = ['_%s.png' % k for k in IMG_SIZE.keys()]
		response_list = self.article.generate_all_thumbnails(dryrun=True)
		for ext in extension_list:
			message = "Generated Image: testfile%s" % ext
			self.assertTrue(message in response_list, msg=message + " not in %s" % response_list)

	def test_base_filename(self):
		expected = 'testfile'
		actual = self.article.base_filename()
		self.assertEqual(expected, actual)

class ViewTest(TestCase):
	"""
	Some quick tests to make sure views dont error out.
	"""

	def setUp(self):
		self.client = Client()
		for num in range(20):
			article = Article(title="Test Article %s" % num, identifier="%s" % num)
			article.save()

	def test_article_list(self):
		url = reverse('articles:list')
		response = self.client.get(url)
		expected = 200
		status_code = response.status_code
		self.assertEqual(expected, status_code)
		expected = 20
		listcount = len(response.context['article_list'])
		self.assertEqual(expected, listcount)

	def test_article_detail(self):
		article_list = Article.objects.all()
		for article in article_list:
			pk = article.id
			url = reverse("articles:detail", args=[pk,])
			expected = 200
			actual = self.client.get(url).status_code
			self.assertEqual(expected, actual)

