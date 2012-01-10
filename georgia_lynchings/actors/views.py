import logging
from django.shortcuts import render
from georgia_lynchings.actors.models import Actor

logger = logging.getLogger(__name__)

def macroevents(request, row_id):
    '''
    List all articles for a
    :class:`~georgia_lynchings.actors.models.Actor`.
    
    :param row_id: the numeric identifier for the 
                   :class:`~georgia_lynchings.actors.models.Actor`.
    '''
    actor = Actor(row_id)
    resultSet = actor.get_macroevents()
    if resultSet:   title = resultSet[0]['actorlabel']
    else:   title = "No records found"    
    return render(request, 'actors/macroevents.html',
                  {'resultSet': resultSet, 'row_id':row_id, 'title':title})    
