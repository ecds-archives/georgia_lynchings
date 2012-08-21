from datetime import datetime
from optparse import make_option
import csv

from django.core.management.base import BaseCommand, CommandError
from georgia_lynchings.articles.models import Article

class Command(BaseCommand):
    args = '<dumpfile name and path>'
    help = """Write a csv export of all article data to the file specified in --dump-path
    """

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("need exactly one argument for the path and filename of the dumpfile.")

        try:
            article_list = Article.objects.all()
            csvWriter = csv.writer(open(args[0], 'wb'))
            csvWriter.writerow(['title', 'publisher', 'date', 'creator', 'filename', 'coverage'])
            for article in article_list:
                row = [
                    article.title,
                    article.publisher,
                    "%s" % article.date,
                    article.creator,
                    article.file,
                    article.coverage,
                ]
                csvWriter.writerow(row)
        except IOError:
            print "Unable to open file args[0] for writing!"

