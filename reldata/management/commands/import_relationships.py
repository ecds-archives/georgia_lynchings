import csv
import datetime
from optparse import make_option

from django.core.management.base import BaseCommand
from georgia_lynchings.reldata import models
from georgia_lynchings.lynchings.models import Story

class Command(BaseCommand):
    help = 'Import relationship data from a CSV report file.'
    args = "<filename>"

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
        'story_id', 'event_id', 'sequence_id', 'triplet_id',
        'subject', 'action', 'object',
    ]

    def set_input_source(self, args):
        'Open the input file or console, and prepare it for CSV input.'

        if args:
            in_file_name = args[0]
            in_file = open(in_file_name, 'rU')
        else:
            import sys
            in_file = sys.stdin

        self.in_csv = csv.DictReader(in_file, fieldnames=self.FIELD_NAMES)

    def wipe_existing_relationships(self):
        '''
        Delete all existing :class:`~georgia_lynchings.reldata.models.Relationship
        objects from the database.
        '''

        models.Relation.objects.all().delete()

    def handle_row(self, row):
        '''
        Handle a single row of CSV input as a dictionary: Parse its field
        values, and create a :class:`~georgia_lynchings.reldata.models.Relationship
        object representing the row.
        '''

        object_properties = {
            'story_id': int(row['story_id']),
            'event_id': int(row['event_id']),
            'sequence_id': int(row['sequence_id']),
            'triplet_id': int(row['triplet_id']),

            'subject': models.Actor.objects.get_or_create(description=row['subject'])[0]
                            if row['subject'] else None,
            'action': models.Action.objects.get_or_create(description=row['action'])[0]
                            if row['action'] else None,
            'object': models.Actor.objects.get_or_create(description=row['object'])[0]
                            if row['object'] else None,
        }

        rel = models.Relation(**object_properties)
        rel.save()
