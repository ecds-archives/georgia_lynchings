from django.db import models
from georgia_lynchings.lynchings.models import Story

class Actor(models.Model):
    """
    A named subject or object in input relationship data.
    """
    description = models.CharField(max_length=80, unique=True)

    def __repr__(self):
        return '<%s: %r>' % (self.__class__.__name__, self.description)


class Action(models.Model):
    """
    A named action in input relationship data.
    """
    description = models.CharField(max_length=80)

    def __repr__(self):
        return '<%s: %r>' % (self.__class__.__name__, self.description)


class Relation(models.Model):
    """
    A relationship between a subject, action, and object in input
    relationship data. Includes links to story and PC-ACE identifiers for
    context.
    """
    story_id = models.PositiveIntegerField()
    event_id = models.PositiveIntegerField()
    sequence_id = models.PositiveIntegerField()
    triplet_id = models.PositiveIntegerField()

    subject = models.ForeignKey(Actor, blank=True, null=True,
                                related_name='relations_as_subject')
    action = models.ForeignKey(Action, blank=True, null=True)
    object = models.ForeignKey(Actor, blank=True, null=True,
                               related_name='relations_as_object')

    def __repr__(self):
        return '<%s: %r -> %r>' % \
            (self.__class__.__name__,
             self.subject.description if self.subject else None,
             self.object.description if self.object else None)
