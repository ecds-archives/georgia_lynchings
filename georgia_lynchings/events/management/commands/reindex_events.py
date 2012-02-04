'''
**reindex_events** is a ``manage.py`` script to reindex project Macro
Events. It reads details about all of the defined Macro Events from the
configured triplestore, and it pushes that data into the configured solr
server.

Example usage
^^^^^^^^^^^^^

Reindex all macro events::

  $ python manage.py reindex_events

'''

import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
import sunburnt

from georgia_lynchings.events.models import MacroEvent, SemanticTriplet, Victim

try:
    from progressbar import ProgressBar, Bar, Percentage, ETA, SimpleProgress, Timer
except ImportError:
    ProgressBar = None

class Command(BaseCommand):
    '''Find all macro events in the triple store, and index them in solr.'''

    help = __doc__

    def handle(self, *args, **options):
        solr = sunburnt.SolrInterface(settings.SOLR_INDEX_URL)
        
        progress = NullProgressBar()
        macs = MacroEvent.all_instances()
        triplets = SemanticTriplet.all_instances()
        victims = Victim.all_instances()        
        items = macs + triplets + victims
        
        if ProgressBar and os.isatty(sys.stdout.fileno()):
            widgets = [Percentage(), ' (', SimpleProgress(), ')', Bar(),
                       ETA()]
            progress = ProgressBar(widgets=widgets, maxval=len(items))

        progress.start()
        for i, obj in enumerate(items):
            idx_data = obj.index_data()
            solr.add(idx_data)
            progress.update(i)

        solr.commit()
        progress.finish()


class NullProgressBar(object):
    '''Expose enough of an interface that code can treat this as a
    do-nothing progress bar for when the real ProgressBar isn't available.
    '''
    def start(self, *args, **kwargs):
        pass
    def update(self, *args, **kwargs):
        pass
    def finish(self, *args, **kwargs):
        pass
