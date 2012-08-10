import glob, os

from django.http import Http404

from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse

from georgia_lynchings.articles.models import Article
from georgia_lynchings.settings import STATIC_ROOT

def article_list(request):
	"""
	Returns a list of all articles.
	"""
	article_list = Article.objects.all()[:50]
	return render(request, 'articles/list.html', {
		'article_list': article_list,
		})

def article_detail(request, article_id):
	"""
	Returns details on an individual article.

	:param article_id:  Local ID number for this article entry.

	"""
	article = get_object_or_404(Article, id=article_id)
	ptrn = "%s/articleimages/%s_page*" % (STATIC_ROOT, article.base_filename())
	raw_imagelist = glob.glob(ptrn)
	pageimage_list = [part.split("/")[-1] for part in raw_imagelist]
	return render(request, 'articles/detail.html',{
        'article': article,
        'pageimage_list': pageimage_list,
        'raw_imagelist': raw_imagelist,
        'ptrn': ptrn,
        })