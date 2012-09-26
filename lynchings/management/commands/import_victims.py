"""
Victim data used throughout the site is a product of exports from PCAce to a 
CSV file in the format listed below.  It can be freely overwritten and is not 
forked or maintained internally.

This import script will wipe and reload all vicitm information and will prompt
the user by default to confirm any data deletion.  It does not wipe any Lynching,
Article or Demogrpahic data.

Usage::
    $ ./manage.py import_victims <filename>

Import File must be in CSV format and contain the following fields in the following 
order:

* event_id - int of PCAce MacroEvent ID 
* date_raw - string of date of attack in format mm/dd/yyyy
* name - string full name of victim
* race_raw - string of victims race
* gender_raw - string of victims gender
* detailed_reason - string of reason stated for lynching
* accusation - string of brief description of reason for lynching
* county - string of county name lynching occured in

**IMPORTANT NOTE:** 

* First row will be ignored as column names.
* Lynching data is not replaced as part of this import, only victim information.

"""

import re, csv
from optparse import make_option
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils.encoding import smart_unicode, smart_str

from georgia_lynchings.demographics.models import County
from georgia_lynchings.lynchings.models import Lynching, Victim, Race, Accusation

class Command(BaseCommand):
    """
    Imports information about Victims of Lynchings for use in rendering the Lynching
    information throughout the site.

    """

    help = "Imports Victim data from the CSV export produced from PCAce.  Ignores first row as fieldnames."
    args = "<filename>"

    fieldnames = ('event_id', 'date_raw', 'name', 'race_raw', 'gender_raw', 'detailed_reason', 'accusation_raw', 'county_raw')

    option_list = BaseCommand.option_list + (
        make_option('--silent',
                action='store_true',
                dest='silent',
                help='Skips user input for the wipe of all victim data before loading input file.'
            ),
        )

    def handle(self, *args, **options):
        if not args:
            raise CommandError("No import file specificed!")
        reader = self._init_reader(args)
        self._confirm_wipe(options.get('silent')) # Safty Step to confirm wipe of data.
        self._insert_count = 0
        for row in reader:
            self._handle_row(row)
        print "Inserted %s Victims from the input file." % self._insert_count

    def _confirm_wipe(self, silent):
        """Step to require users to confirm the wipe of victims before proceeding."""
        if not silent:
            input_msg = """CONFIRM YOU WISH TO PROCEED WITH A FULL WIPE AND RELOAD OF \
                        ALL VICTIM, RACE and ACCUSATION DATA? (Y/n)"""
            user_input = raw_input(input_msg + ': ')
            if user_input.lower() not in ['y', 'yes']:
                raise CommandError("User Aborted Data Import!  No data was changed.")
            print "Wiping %s Victims from the database." % Victim.objects.all().count()
            Victim.objects.all().delete()
            Accusation.objects.all().delete()
            Race.objects.all().delete()

    def _init_reader(self, *args):
        """Open the input file and return the reader object."""

        try:
            filename = "%s" % args[0]
            f = open(filename, 'rb')
            reader = csv.DictReader(f, fieldnames=self.fieldnames)
            reader.next()
            return reader
        except IOError as e:
            raise CommandError("Unable to find file %s" % filename)

    def _handle_row(self, row):
        """
        Processes a single row from the input file.

        :param row:  Dict of a single raw input row.
        """
        data = {
            'name': smart_unicode(row['name'], errors='ignore'),
            'detailed_reason': smart_unicode(row['detailed_reason'], errors='ignore'),
        }
        data['lynching'], created = Lynching.objects.get_or_create(pca_id=row['event_id'])
        data['race'] = self._get_race(row['race_raw'])
        data['gender'] = self._get_gender(row['gender_raw'])
        data['county'] = self._get_county(row['county_raw'])
        data['date'] = self._handle_date(row['date_raw'])
        victim = Victim(**data)
        victim.save()
        self._handle_accusation(victim, row['accusation_raw'])
        self._insert_count += 1

    def _get_race(self, race_raw):
        """
        Tries to approximate a match of race from current values or creates one if no match found.
        """
        if not race_raw:
            return None
        race_text = race_raw.strip(' \t\n\r')
        try:
            race = Race.objects.get(label__iexact=race_text)
        except Race.DoesNotExist:
            race = Race(label=race_text)
            race.save()
        return race

    def _get_gender(self, gender_raw):
        """
        Tries to match the sex listed in the input string to one of our gender options.
        """
        if not gender_raw:
            return None
        gender = gender_raw.strip(' \t\n\r')
        if gender.lower() in ['male', 'man', 'boy', 'men']:
            return 'M'
        if gender.lower() in ['female', 'woman', 'girl']:
            return 'F'
        return None

    def _handle_date(self, date_string):
        """
        Returns a date object parsed from date_string.
        """
        try:
            fmt = "%m/%d/%Y"# mm/dd/yyyy
            date = datetime.strptime(date_string.strip(), fmt)
            return date
        except ValueError:
            #print("Could not parse date from string %s" % date_string)
            return None
        
    def _handle_accusation(self, victim, accusation_raw):
        """
        Tries to approximate a match of the accusation from the current values or creates one if no match found.
        """
        if not accusation_raw:
            return None
        accusation_text = accusation_raw.strip(' \t\n\r')
        try:
            accusation = Accusation.objects.get(label__iexact=accusation_text)
        except Accusation.DoesNotExist:
            accusation = Accusation(label=accusation_text)
            accusation.save()
        victim.accusation.add(accusation)

    def _get_county(self, county_raw):
        """
        This processes the string data from the county information and tries to make a
        sensible match from it.
        """
        if not county_raw:
            return None
        county_name = county_raw.strip(' \t\n\r')
        try:
            county = County.objects.get(name__iexact=county_name)
            return county
        except County.DoesNotExist:
            print "County named %s not found in list!" % county_name
            return None



