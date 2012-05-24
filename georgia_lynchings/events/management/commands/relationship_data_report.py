import csv
import sys
from django.core.management.base import BaseCommand
from georgia_lynchings.events.models import SemanticTriplet

class Command(BaseCommand):
    help = """
        Output a CSV report containing information about subjects,
        processes, and objects of encoded sentences (triplets) in PC-ACE RDF
        data.

        This output is designed to approximate a report generated from
        PC-ACE by the project PI. Currently this output contains very
        similar data but much more of it. It's not clear whether additional
        automatic filtering is possible or if the report naturally requires
        manual processing before further use.
        """

    def handle(self, *args, **options):
        triplets = self.fetch_triplets()

        csvout = csv.writer(sys.stdout)
        csvout.writerow(self.header_row())
        for triplet in triplets:
            for row in self.triplet_rows(triplet):
                csvout.writerow(row)


    def fetch_triplets(self):
        """
        Fetch all :class:`~georgia_lynchings.events.models.SemanticTriplet`
        objects, pre-fetchings fields that will be used for this command.
        """

        FETCH_FIELDS = [
            'participant_s__individuals__actor_name',
            'participant_s__individuals__first_name',
            'participant_s__individuals__last_name',
            'participant_s__individuals__gender',
            'participant_s__individuals__race',
            'participant_s__individuals__qualitative_age',
            'participant_s__individuals__exact_age',
            'participant_s__individuals__type_of_actor',
            'process__verbal_phrase',
            'process__definite_date',
            'process__city_name',
            'process__reason_name',
            'process__instrument_name',
            'participant_o__individuals__actor_name',
            'participant_o__individuals__gender',
            'participant_o__individuals__race',
            ]
        return SemanticTriplet.objects.fields(*FETCH_FIELDS).all()

    def header_row(self):
        """
        Return a CSV row (as a Python list) representing column headers.
        Header names are drawn from an example file manually generated by
        project PI. Each column corresponds to a single column from
        :meth:`triplet_rows`.
        """
        return [# grouped as in triplet_rows() below
                # triplet
                'Sentence ID',
                # participant_s 
                'Node1 ID', 'Node1 value', 'First name', 'Last name',
                'Gender', 'Race', 'Qualitative age', 'Exact age',
                'Type of actor (Adjective)',
                # process
                'Relation ID', 'Relation value', 'Definite date',
                'City name', 'Name of reason', 'Type of instrument',
                # participant_o
                'Node2 ID', 'Node2 Value', "Gender'", "Race'",
               ]

    def triplet_rows(self, triplet):
        """
        Yield CSV rows (each as a Python list) representing a single output
        row. For each triplet, a row is generated for each
        subject/process/object combination in that triplet. Each item in
        that row corresponds to a column from the :meth:`header_row`.
        """
        p = triplet.process
        if p:
            for ps in triplet.participant_s:
                for s in ps.individuals:
                    for po in triplet.participant_o:
                        for o in po.individuals:
                            yield [# grouped as in header_row() above
                                   # triplet
                                   triplet.id,
                                   # participant_s
                                   s.id, s.actor_name, s.first_name, s.last_name,
                                   s.gender, s.race, s.qualitative_age, s.exact_age,
                                   s.type_of_actor,
                                   # process
                                   p.id, p.verbal_phrase, p.definite_date,
                                   p.city_name, p.reason_name, p.instrument_name,
                                   # participant_o
                                   o.id, o.actor_name, o.gender, o.race,
                                  ]
