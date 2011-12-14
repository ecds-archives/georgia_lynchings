import logging
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from georgia_lynchings.events.event import Event

logger = logging.getLogger(__name__)

def articles(request, row_id):
    "Get articles for event."
    '''
    row_id: macro event id.  Example dcx:r12
    '''    
    event = Event()
    resultSet = event.get_articles(row_id)
    title = resultSet[0]['melabel']['value']
    return render(request, 'events/articles.html',
                  {'resultSet': resultSet, 'row_id':row_id, 'title':title})    
