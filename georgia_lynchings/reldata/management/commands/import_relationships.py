import csv
import datetime
from optparse import make_option

from django.core.management.base import BaseCommand
from georgia_lynchings.reldata.models import Relationship

class Command(BaseCommand):
    help = 'Import relationship data from a CSV report file.'

    option_list = BaseCommand.option_list + (
        make_option('--wipe',
            action='store_true',
            help='Remove all existing relationships from the database before loading new ones'),
    )

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])

        # set input source before wiping: it seems rude to wipe the db if we
        # can't even open the input file
        self.set_input_source(args)
        skipped_header = self.in_csv.next()

        if options['wipe']:
            if verbosity > 1:
                print 'Wiping existing relationships from database'
            self.wipe_existing_relationships()

        row_count = 0
        for row in self.in_csv:
            self.handle_row(row)
            row_count += 1

        if verbosity > 1:
            print 'Added %d new relationships' % (row_count,)

    # field names in the order they appear in the input csv file. since
    # there's a one-to-one mapping between csv fields and Relationship
    # fields, we give them the same names.
    FIELD_NAMES = [
        'triplet_id',

        'subject_id', 'subject_desc', 'subject_first_name', 'subject_last_name',
        'subject_gender', 'subject_race', 'subject_age_desc', 'subject_exact_age',
        'subject_adjective',

        'process_id', 'process_desc', 'process_date', 'process_city', 'process_reason',
        'process_instrument',

        'object_id', 'object_desc', 'object_gender', 'object_race',
    ]

    def set_input_source(self, args):
        'Open the input file or console, and prepare it for CSV input.'

        if args:
            in_file_name = args[0]
            in_file = open(in_file_name)
        else:
            import sys
            in_file = sys.stdin

        self.in_csv = csv.DictReader(in_file, fieldnames=self.FIELD_NAMES)

    def wipe_existing_relationships(self):
        '''
        Delete all existing :class:`~georgia_lynchings.reldata.models.Relationship
        objects from the database.
        '''

        Relationship.objects.all().delete()

    def handle_row(self, row):
        '''
        Handle a single row of CSV input as a dictionary: Parse its field
        values, and create a :class:`~georgia_lynchings.reldata.models.Relationship
        object representing the row.
        '''

        object_properties = {}
        for key, val in row.iteritems():
            process = getattr(self, 'parse_' + key,
                              self.parse_default_field)
            object_properties[key] = process(val)

        rel = Relationship(**object_properties)
        rel.save()

    def parse_default_field(self, val):
        '''
        By default, represent all field values as strings, replacing missing
        (``None``) values with empty strings.
        '''
        return val or ''

    def parse_triplet_id(self, val):
        'The ``triplet_id`` is an integer field.'
        if val:
            return int(val)

    def parse_subject_id(self, val):
        'The ``subject_id`` is an integer field.'
        if val:
            return int(val)

    def parse_subject_exact_age(self, val):
        'The ``subject_exact_age`` is an integer field.'
        if val:
            return int(val)

    def parse_process_id(self, val):
        'The ``process_id`` is an integer field.'
        if val:
            return int(val)

    def parse_process_date(self, val):
        'The ``process_date`` is a date field.'
        if val:
            dt = datetime.datetime.strptime(val, '%m/%d/%Y')
            return dt.date()

    def parse_object_id(self, val):
        'The ``object_id`` is an integer field.'
        if val:
            return int(val)
