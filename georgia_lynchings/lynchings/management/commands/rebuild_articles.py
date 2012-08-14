import csv

from django.core.management.base import BaseCommand, CommandError
from django.utils.encoding import smart_unicode, smart_str

from georgia_lynchings.articles.models import Article
from georgia_lynchings.lynchings.models import Lynching

class Command(BaseCommand):
    help = "Related articles to lynchings by the PCA Identifier in th import file."
    args = "<filename>"
    fieldnames = ('event_id', 'article_id', 'filename', 'victim_name')


    def handle(self, *args, **options):
    	reader = self._init_reader(args)
        for row in reader:
            self._handle_row(row)

    def _handle_row(self, row):
        """
        Handles data from an individual row in the import file.
        """
        try: 
            lynching = Lynching.objects.get(pca_id=row['event_id'])
            try:
                article = Article.objects.get(identifier=row['article_id'])
                lynching.articles.add(article)
            except Article.DoesNotExist:
                print("No Article with PCAce ID %s" % row["article_id"])
        except Lynching.DoesNotExist:
            print("No Lynching for PCAce ID %s Found!" % row['event_id'])

    def _init_reader(self, *args):
        """Open the input file and return the reader object."""

        try:
            filename = "%s" % args[0]
            self.csv_file = open(filename, 'rU')
            reader = csv.DictReader(self.csv_file, fieldnames=self.fieldnames)
            reader.next()
            return reader
        except IOError as e:
            raise CommandError("Unable to find file %s" % filename)