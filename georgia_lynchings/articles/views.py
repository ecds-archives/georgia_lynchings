import logging
from django.shortcuts import render
from georgia_lynchings.articles.models import all_articles

logger = logging.getLogger(__name__)

def newspaper_articles(request):
    '''
    List all articles in the database.
    '''

    # FIXME: all_articles is deprecated. we need code in this module to
    # fetch either Article.objects.all() or PcAceDocument.objects.all() with
    # the .fields() we want to access.
    resultSet = all_articles()
    if resultSet:   title = "%d Articles" % len(resultSet)
    else:   title = "No records found"    
    return render(request, 'articles/all_articles.html',
                  {'resultSet': resultSet, 'title':title})                 
