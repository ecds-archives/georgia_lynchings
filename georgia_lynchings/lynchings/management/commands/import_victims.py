import re
from optparse import make_option
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from georgia_lynchings.events.models import Victim
from georgia_lynchings.demographics.models import County
from georgia_lynchings.lynchings.models import Person, Lynching, Story, Race, \
    Alias, Accusation

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
            lynching = self._handle_lynching(victim, **options)

    def _handle_person(self, victim, **options):
        person, created = Person.objects.get_or_create(pca_id=victim.id)
        person.pca_last_update = datetime.now()
        if not person.race and victim.race or options['overwrite']:
            race, race_created = Race.objects.get_or_create(label=victim.race)
            if race_created:
                race.save()
            person.race = race
        if not person.name and victim.primary_name or options['overwrite']:
            person.name = unicode(victim.primary_name)
        if not person.gender and victim.gender or options['overwrite']:
            genders = ['male', 'female']
            try:
                if genders.index(victim.gender.lower()) == 0:
                    person.gender = 'M'
                else:
                    person.gender = 'F'
            except ValueError:
                pass
        person.save()
        if victim.all_names:
            # Get unique list of alt names not already the primary name
            name_list = set(victim.all_names).difference(set(person.name))
            for name in name_list:
                alias, alias_created = Alias.objects.get_or_create(name=unicode(name), person=person)
                alias.save()
        person.save()
        return person

    def _handle_lynching(self, victim, **options):
        try:
            person = Person.objects.get(pca_id=victim.id)
        except Person.DoesNotExist:
            raise CommandError("Error trying to create Lynching for a Person that does not exist.")
        story, story_created = Story.objects.get_or_create(pca_id=victim.macro_event.id)
        if story_created or not story.pca_last_update:
            story.pca_last_update = datetime.now()
            story.save()
        lynching, created = Lynching.objects.get_or_create(victim=person, pca_id=person.pca_id, story=story)

        # primary date of lynching.
        if not lynching.date and victim.primary_lynching_date or options['overwrite']:
            lynching.date = victim.primary_lynching_date

        # handle alleged crime
        if not lynching.alleged_crime and victim.primary_alleged_crime or options['overwrite'] and victim.primary_alleged_crime:
            accusation, acc_created = Accusation.objects.get_or_create(label=victim.primary_alleged_crime)
            lynching.alleged_crime = accusation

        # handle county
        county_list = self._handle_counties(victim)
        if not lynching.county and county_list or options['overwrite'] and county_list:
            lynching.county = county_list[0]
            county_list.pop(0)

        lynching.pca_last_update = datetime.now()
        lynching.save()  # Save before adding many to many rels

        # Now handle many to many relationships.
        for county in county_list:
            lynching.alternate_counties.add(county)     # handle alternate county

        return lynching

    def _handle_counties(self, victim):
        """
        This processes the string data from the county information and tries to make a
        sensible list from it.
        """
        # county is sometimes a string of multiple counties
        word_list = []
        county_names = self._county_names()
        for raw_county in victim.all_counties:
            word_list.extend(self._clean_county_string(raw_county))
        county_list = []
        for word in set(word_list):
            if word in county_names and word not in county_list:
                county_list.append(County.objects.get(name__iexact=word))
        return county_list

    def _county_names(self):
        """
        Gets a set of normalized county names.
        """
        counties = County.objects.all()
        return set([county.name.lower() for county in counties])

    def _clean_county_string(self, raw_string):
        """
        Processes a raw string literal to return a list of lowercase unique words.
        """
        return [re.sub('[^a-zA-Z]','', part).lower() for part in raw_string.split(" ")]



