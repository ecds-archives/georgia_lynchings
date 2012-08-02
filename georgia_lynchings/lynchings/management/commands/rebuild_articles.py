import csv

from django.core.management.base import BaseCommand, CommandError
from django.utils.encoding import smart_unicode, smart_str

from georgia_lynchings.articles.models import Article
from georgia_lynchings.lynchings.models import Lynching

class Command(BaseCommand):
    help = "Imports Victim data from the CSV export produced from PCAce.  Ignores first row as fieldnames."

    fieldnames = ('event_id', 'article_id', 'filename', 'victim_name')


    def handle(self, *args, **options):
    	reader = self._init_reader(args)
        new_ids = set()
        article_event_ids = set()
        for row in reader:
            new_ids.add(int(row['article_id']))
            article_event_ids.add(int(row['event_id']))
    	old_ids = set([int(article.identifier) for article in Article.objects.all()])
        print "There are %s old IDs not found in the new set." % len(new_ids.difference(old_ids))
        print "There are %s new IDs" % len(old_ids.difference(new_ids))
    	
        event_ids = set([lynching.pca_id for lynching in Lynching.objects.all()])
        print "%s Lynchings have no articles associated." % len(event_ids.difference(article_event_ids))
        print "%s articles have no Lynchings related to them." % len(article_event_ids.difference(article_event_ids))

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