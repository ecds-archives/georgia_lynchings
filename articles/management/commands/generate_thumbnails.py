from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from georgia_lynchings.articles.models import Article

class Command(BaseCommand):
    help = """Generate all size thumbnails for articles."""

    option_list = BaseCommand.option_list + (
        make_option('--recreate',
            dest='recreate',
            action='store_true',
            default=False,
            help="Recreate thumbnails even if they already exist."),
        )

    def handle(self, *args, **options):
        article_list = Article.objects.all()
        recreate = False
        if options['recreate']: # I  know it is wierd, but I'm tired and it's late.
            recreate = True
        for article in article_list:
            article.generate_all_thumbnails(recreate)


