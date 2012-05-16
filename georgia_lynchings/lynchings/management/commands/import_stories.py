from optparse import make_option
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from georgia_lynchings.events.models import MacroEvent
from georgia_lynchings.lynchings.models import Story

class Command(BaseCommand):
    help = "Imports Macro Event information from the PC-ACE rdf triplestore info."

    option_list = BaseCommand.option_list + (
        make_option('--overwrite',
            action='store_true',
            dest='overwrite',
            default=False,
            help='Overwrite data in forked model with original data'),
        )

    def handle(self, *args, **options):
        event_list = MacroEvent.objects.all()
        for event in event_list:
            story, created = Story.objects.get_or_create(pca_id=event.id)
            if options['overwrite'] or created:
                story.pca_last_update = datetime.now()
            story.save()
