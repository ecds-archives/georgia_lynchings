from datetime import datetime
from optparse import make_option
import os
import re

from django.core.files import File
from django.core.management.base import NoArgsCommand
from georgia_lynchings.articles.models import Article, PcAceDocument

class Command(NoArgsCommand):
    help = """Import all PC-ACE document metadata from the triplestore and
    file data from the local filesystem into the Django database for
    management inside the app.
    """

    option_list = NoArgsCommand.option_list + (
        make_option('--simulate', '-n',
            action='store_true',
            help="Don't add or change data; only output what would be done"),
        make_option('--article-path', '-a',
            default='',
            help="Path to article file data"),
        )

    def handle_noargs(self, verbosity=1, simulate=False, article_path='', **options):
        self.verbosity = int(verbosity)
        self.simulate = simulate
        self.article_path = os.path.expanduser(article_path)

        PRELOAD_FIELDS = ['id', 'newspaper_name', 'newspaper_date',
                          'page_number', '_pdf_path']
        docs = list(PcAceDocument.objects.fields(*PRELOAD_FIELDS).all())
        if self.verbosity > 1:
            print 'Importing %d documents.' % (len(docs),)

        for doc in docs:
            self.import_document(doc)


    def import_document(self, doc):
        '''Import a single :class:`~georgia_lynchings.articles.models.PcAceDocument`.'''

        id = doc.id
        if id is None:
            if self.verbosity > 0:
                print 'Failed to import document %s: no id' % (doc.uri.n3(),)
            return
        
        filename = doc.pdf_filename
        if filename is None:
            if self.verbosity > 1:
                print 'No filename for %s.' % (doc.uri.n3(),)
            filename_bits = {}
        else:
            filename_bits = self.parse_filename(filename)
        
        def _get_field(name, desc):
            val = getattr(doc, name, None)
            if val is None:
                if name in filename_bits:
                    val = filename_bits[name]
                    if self.verbosity > 2:
                        print 'No %s for %s. Inferring from filename.' % (desc, doc.uri.n3())
                else:
                    if self.verbosity > 2:
                        print 'No %s for %s. Importing without that value.' % (desc, doc.uri.n3())
            return val

        newspaper_name = _get_field('newspaper_name', 'newspaper name')
        newspaper_date = _get_field('newspaper_date', 'newspaper date')
        page_number = _get_field('page_number', 'page')

        # Even if we're simulating, make the Article just to verify that we
        # can. Simulate should stop at the last possible moment to catch as
        # many errors as possible. In particular, this should verify that
        # the file is readable.
        try: # Can't use get_or_create because that autosaves on creation.
            article = Article.objects.get(identifier=doc.uri)
            created = False
        except Article.DoesNotExist:
            article = Article()
            created = True

        input_file = None
        try:
            if filename and not article.file:
                try:
                    filepath = os.path.join(self.article_path, filename)
                    input_file = open(filepath)
                    article.file = File(input_file)
                except IOError:
                    if self.verbosity > 0:
                        print 'Failed to import document %s: failed to read file "%s"' % \
                                (doc.uri.n3(), filepath)
                    return

            if created:
                article.identifier = doc.uri
                if newspaper_name:
                    article.publisher = newspaper_name
                if newspaper_date:
                    article.date = newspaper_date
                if page_number:
                    article.coverage = page_number

            if not self.simulate:
                article.save()

        finally:
            if input_file is not None:
                input_file.close()

        if self.verbosity > 1:
            print 'Import: %s %s,%s,%s,%s,%s' % (
                    '(simulated)' if self.simulate
                                  else ('Article %d := ' % (article.id),),
                    id,
                    repr(filename) if filename else '',
                    repr(unicode(newspaper_name)) if newspaper_name else '',
                    newspaper_date or '',
                    page_number or '',
                )


    FILENAME_RE = re.compile(r'''(?P<newspaper_name>[^_]+)_
                                 (?P<newspaper_date>\d\d-\d\d-\d\d\d\d)_
                                 (?P<page_number>[^_]+)
                                 \.pdf''',
                             re.X)
    def parse_filename(self, filename):
        '''Guess article metadata from the filename. Returns a dictionary
        with keys of :class:`~~georgia_lynchings.articles.models.PcAceDocument`
        properties of data found in the filename. Returned dictionary values
        are the inferred field values.
        '''

        match = self.FILENAME_RE.match(filename)
        if match is None:
            if self.verbisity > 2:
                print 'Unable to parse filename %r.' % (filename,)
                return {}
        groups = match.groupdict()
        if 'newspaper_date' in groups: # it should be
            dt_val = datetime.strptime(groups['newspaper_date'], '%m-%d-%Y')
            # replace it with parsed version
            groups['newspaper_date'] = dt_val.date()

        return groups
