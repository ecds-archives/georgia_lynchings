from optparse import make_option
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from georgia_lynchings.events.models import Victim
from georgia_lynchings.lynchings.models import Person, Lynching, Story, Race, \
    County, Alias, Accusation

class Command(BaseCommand):
    help = "Imports Macro Event information from the PC-ACE rdf triplestore info."

    option_list = BaseCommand.option_list + (
        make_option('--overwrite',
            action='store_true',
            dest='overwrite',
            default=False,
            help='Overwrite data in forked model with original data from PC-Ace'),
        )

    def handle(self, *args, **options):
        victim_list = Victim.objects.all()
        for victim in victim_list:
            person = self._handle_person(victim, **options)
            person.save()
            #lynching = self._handle_lynching(victim, person, **options)
            #lynching.save()

    def _handle_person(self, victim, **options):
        person, created = Person.objects.get_or_create(pca_id=victim.id)
        person.pca_last_update = datetime.now()
        if not person.race and victim.race or options['overwrite']:
            race, race_created = Race.objects.get_or_create(label=victim.race)
            if race_created:
                race.save()
            person.race = race
        if not person.name and victim.primary_name or options['overwrite']:
            person.name = victim.primary_name
        if not person.gender and victim.gender or options['overwrite']:
            genders = ['male', 'female']
            try:
                if genders.index(victim.gender.lower()) == 0:
                    person.gender = 'M'
                else:
                    person.gender = 'F'
            except ValueError:
                pass
        # handle alias
        return person

    def _handle_lynching(self, victim, person, **options):
        lynching, created = Lynching.objects.get_or_create(pca_id=victim.id)
        # handle person
        # handle county
        # handle alleged crime
        # handle alternate county
        # handle story
        return lynching

