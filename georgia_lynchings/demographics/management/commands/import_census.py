import csv
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from georgia_lynchings.demographics.models import County, Population

class Command(BaseCommand):
    # This is highly specific and probably only useable once.
    help = "Import Census data from a csv export file."

    option_list = BaseCommand.option_list + (
        make_option('--purge',
            action='store_true',
            dest='purge',
            default=False,
            help='Empty population data before importing.'),
        )

    def handle(self, *args, **options):
        if options["purge"]:
            Population.objects.all().delete()
        years = [1870, 1880, 1890, 1900, 1910, 1920, 1930]
        for year in years:
            self._import_file(year)

    def _import_file(self, year):
        """
        Imports a specific cencus data file.
        """
        dataReader = csv.DictReader(open("%s.csv" % year, 'rUb'))
        for row in dataReader:
            county, created = County.objects.get_or_create(name=row['county'].title())
            if created:
                county.save()
                print "%s not found!  Created." % county.name
            pop = Population(county=county, year=row['year'])
            if row['total']:
                pop.total = row['total']
            if row['white']:
                pop.white = row['white']
            if row['black']:
                pop.black = row['black']
            if row['iltr_white']:
                pop.iltr_white = row['iltr_white']
            if row['iltr_black']:
                pop.iltr_black = row['iltr_black']
            pop.save()