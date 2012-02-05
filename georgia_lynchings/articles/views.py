import logging
from django.core.urlresolvers import reverse
from django.shortcuts import render
from georgia_lynchings.articles.models import all_articles

logger = logging.getLogger(__name__)

def newspaper_articles(request):
    '''
    List all articles for a
    :class:`~georgia_lynchings.articles.models.NewspaperArticles`.
    '''

    resultSet = all_articles()
    if resultSet:   title = "%d Articles" % len(resultSet)
    else:   title = "No records found"    
    # FIXME: use reverse here
    return render(request, 'articles/all_articles.html',
                  {'resultSet': resultSet, 'title':title})                 
