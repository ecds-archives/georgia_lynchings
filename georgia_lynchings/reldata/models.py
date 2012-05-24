from django.db import models

class Relationship(models.Model):
    """
    A relationship between individuals through some action. This model
    directly represents information imported from a flat data file. The
    triplet_id represents an encoded triplet from a PC-ACE database. Each
    row represents some combination of subject, process, and object from
    that triplet. A triplet with multiple individuals in its subject or
    object may be represented multiple times.

    This model is denormalized: In a normalized structure the actors
    (subject and object) and process would be separate models, and this
    Relationship would tie them together by reference. Instead we're leaving
    them all in a single model: For now the value of closely representing
    the input data format is greater than the value of the normalization. If
    that changes, then it may be sensible to normalize the schema.
    """
    help = {
        'triplet_id': 'Row number for Semantic Triplet PC-ACE object for this data',

        'subject_id': 'Row number for Individual PC-ACE object for a subject of this triplet',
        'subject_desc': 'Text short-name ("Name of individual actor") of this subject individual',
        'subject_first_name': 'First name of this subject individual',
        'subject_last_name': 'Last name of this subject individual',
        'subject_gender': 'Gender of this subject individual (not normalized)',
        'subject_race': 'Race of this subject individual (not normalized)',
        'subject_age_desc': 'Text description of the age ("Qualitative age") of this subject individual',
        'subject_exact_age': 'Numeric age of this subject individual',
        'subject_adjective': 'Alternate descriptor ("Type of actor (Adjective)") of this subject individual',

        'process_id': 'Row number for Simple Process PC-ACE object for the process of this triplet',
        'process_desc': 'Short phrase ("Verbal phrase") describing this process',
        'process_date': 'Date this process happened',
        'process_city': 'A city associated with this process; typically where it happened',
        'process_reason': 'A reason given for the action of this process, typically from a biased source',
        'process_instrument': 'An object used in the action of this process',

        'object_id': 'Row number for Individual PC-ACE object for an object of this triplet',
        'object_desc': 'Text short-name ("Name of individual actor") of this object individual',
        'object_gender': 'Gender of this object individual (not normalized)',
        'object_race': 'Race of this object individual (not normalized)',
    }
    triplet_id = models.PositiveIntegerField(db_index=True, help_text=help['triplet_id'])

    subject_id = models.PositiveIntegerField(blank=True, null=True, db_index=True, help_text=help['subject_id'])
    subject_desc = models.CharField(max_length=30, blank=True, help_text=help['subject_desc'])
    subject_first_name = models.CharField(max_length=30, blank=True, help_text=help['subject_first_name'])
    subject_last_name = models.CharField(max_length=30, blank=True, help_text=help['subject_last_name'])
    subject_gender = models.CharField(max_length=30, blank=True, help_text=help['subject_gender'])
    subject_race = models.CharField(max_length=30, blank=True, help_text=help['subject_race'])
    subject_age_desc = models.CharField(max_length=30, blank=True, help_text=help['subject_age_desc'])
    subject_exact_age = models.IntegerField(blank=True, null=True, help_text=help['subject_exact_age'])
    subject_adjective = models.CharField(max_length=60, blank=True, help_text=help['subject_adjective'])

    process_id = models.PositiveIntegerField(blank=True, null=True, db_index=True, help_text=help['process_id'])
    process_desc = models.CharField(max_length=30, blank=True, help_text=help['process_desc'])
    process_date = models.DateField(blank=True, null=True, help_text=help['process_date'])
    process_city = models.CharField(max_length=30, blank=True, help_text=help['process_city'])
    process_reason = models.CharField(max_length=60, blank=True, help_text=help['process_reason'])
    process_instrument = models.CharField(max_length=30, blank=True, help_text=help['process_instrument'])

    object_id = models.PositiveIntegerField(blank=True, null=True, db_index=True, help_text=help['object_id'])
    object_desc = models.CharField(max_length=30, blank=True, help_text=help['object_desc'])
    object_gender = models.CharField(max_length=30, blank=True, help_text=help['object_gender'])
    object_race = models.CharField(max_length=30, blank=True, help_text=help['object_race'])

