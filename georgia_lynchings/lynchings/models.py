from django.db import models

EVENT_CHOICES = (
    ('Lynching', "LN"),
)
GENDER_CHOICES = (
    ('Male', 'M'),
    ('Female', 'F'),
)

class Lynching(models.Model):
    """
    Class to represent an overall lynching event.
    """
    pass # TODO: Implement

class Event(models.Model):
    """
    Represents an invididual event
    """
    lynching = models.ForeignKey(Lynching, help_text="Lynchning this corrisponds to.")
    type = models.CharField(max_length=2, choices=EVENT_CHOICES, default=EVENT_CHOICES[0])
    county = models.ForeignKey(County, null=True, blank=True, help_text="Primary county it took place in.")
    alternate_counties = models.ManyToManyField(County) # List alternate possible counties here.
    date = models.DateField(null=True, blank=True, help_text="Date of event.")
    target = models.ForeignKey(Person, null=True, blank=True)
    # alleged_crime ??
    #

class County(models.Model):
    """
    Class to represent county demographic and geospacial information.
    """
    name = models.CharField(max_length=50, help_text="Name of County.")
    latitude = models.FloatField()
    longitude = models.FloatField()

class Alias(models.Model):
    """
    Alternative names or aliases used by people.
    """
    name_help = "Other or alternate names used"
    name = models.CharField(max_length=75, help_text=name_help)
    person = models.ForeignKey(Person, help_text="Person alias applies to.")

class Person(models.Model):
    """
    Class to represent data about a person involved in a lynching.
    """
    name_help = "Most authoritative full name of victim."
    name = models.CharField(max_length=75, null=True, blank=True, help_text=name_help)
    # race ??  Choice list for consitency?
    gender = models.CharField(max_length=1, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    # occupation ??
    # status ??
    # mob_type from brundage
