import logging
from django.shortcuts import render
from georgia_lynchings.articles.models import NewspaperArticles

logger = logging.getLogger(__name__)

def newspaper_articles(request):
    '''
    List all articles for a
    :class:`~georgia_lynchings.articles.models.NewspaperArticles`.
    
    :param row_id: the numeric identifier for the 
                   :class:`~georgia_lynchings.articles.models.NewspaperArticles`.
    '''
    newspaper_articles = NewspaperArticles()
    resultSet = newspaper_articles.all_articles()
    if resultSet:   title = "%d Articles" % len(resultSet)
    else:   title = "No records found"    
    return render(request, 'articles/all_articles.html',
                  {'resultSet': resultSet, 'title':title})                 
