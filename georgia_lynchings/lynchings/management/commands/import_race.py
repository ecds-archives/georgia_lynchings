from optparse import make_option
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from georgia_lynchings.events.models import Victim
from georgia_lynchings.lynchings.models import Race

class Command(BaseCommand):
    help = "Imports Race Choices for People in the database from the PC-ACE data."

    def handle(self, *args, **options):
        victim_list = Victim.objects.all()
        race_set = set([victim.race for victim in victim_list if victim.race])
        for race in race_set:
            obj, created = Race.objects.get_or_create(label=race)
            if created: # Only save new entries, we shouldn't overwrite this.
                obj.save()


