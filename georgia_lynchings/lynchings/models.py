from django.db import models
from django.utils.encoding import smart_str

from georgia_lynchings.articles.models import Article

# Tuples and classes use for controlled vocab and choices
GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
)

class Accusation(models.Model):
    """
    Represents the alleged crimes.
    """
    label_help = "Text used to classify alleged crime."
    label = models.CharField(max_length=75, help_text=label_help)

    # String Methods
    def __unicode__(self):
        return u'%s' % self.label
    def __str__(self):
        return smart_str(self.__unicode__())

    class Meta:
        ordering = ['label',]

class Race(models.Model):
    """
    Represents a list of races to use for people.
    """
    label = models.CharField(max_length=50, help_text="Label to used for individual race.")

    # String Methods
    def __unicode__(self):
        return u'%s' % self.label
    def __str__(self):
        return smart_str(self.__unicode__())

class County(models.Model):
    """
    Class to represent county demographic and geospacial information.
    """
    label = models.CharField(max_length=50, help_text="Name of County.", unique=True, db_index=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    # String Methods
    def __unicode__(self):
        return u'%s' % self.label
    def __str__(self):
        return smart_str(self.__unicode__())

    class Meta:
        verbose_name_plural = "counties"
        ordering = ["label"]


# Classes to represent forked data models for PC-ACE Complex objects.
class Story(models.Model):
    """
    Class to represent a connected sequence of events for an overall lynching.
    PC-ACE Complex Object:  MacroEvent
    """
    help = {
        'pcaid': "Row number for Macro Event complex object in PC-ACE",
        'pcalastupdate': "Datetime of the last sync with PC-Ace Data.",
    }
    pca_id = models.PositiveIntegerField(help_text=help['pcaid'], unique=True, db_index=True)
    pca_last_update = models.DateTimeField(null=True, blank=True, editable=False, help_text=help["pcalastupdate"])

    articles = models.ManyToManyField(Article, help_text="Related Documents and Files")

    @property
    def pretty_string(self):
        """
        Returns a more descriptive string for the story.
        """
        string_parts = [u'Lynching of',]
        string_parts.append(u", ".join([u"%s" % lynching.victim for lynching in self.lynching_set.all()]))
        date_set = set([u"%s" % lynching.date.year for lynching in self.lynching_set.all() if lynching.date])
        if date_set:
            string_parts.append(u"in %s" % ", ".join(date_set))
        return u" ".join(string_parts)

    @property
    def county_list(self):
        """
        Convienence method to generate a list of all counties.
        """
        county_list = []
        for lynching in self.lynching_set.all():
            county_list.append(lynching.county)
            county_list.extend([county for county in lynching.alternate_counties.all()])
        return list(set(county_list))

    @property
    def year(self):
        """
        Best determination of date of lynching.
        """
        year_list = sorted([lynching.date.year for lynching in self.lynching_set.all() if lynching.date])
        if year_list:
            return year_list[-1] # return the highest date
        return None

    # String Methods
    def __unicode__(self):
        return u'%s' % self.pretty_string
    def __str__(self):
        return smart_str(self.__unicode__())

    class Meta:
        verbose_name_plural = "stories"

class Person(models.Model):
    """
    Class to represent data about a person involved in a lynching.
    PC-ACE Complex Object:  Victim (partial)
    """
    help = {
        'pcaid': "Row number for Victim complex object in PC-ACE",
        "pcalastupdate": "Datetime of last update from PC-Ace",
        'name': "Most reliable full or display name for person.",
        'race': "Race of person.",
        'age': "Most reliable reported age of person",
    }
    pca_id = models.PositiveIntegerField(help_text=help['pcaid'], unique=True, db_index=True, editable=False)
    pca_last_update = models.DateTimeField(null=True, blank=True, editable=False, help_text=help["pcalastupdate"])
    name = models.CharField(max_length=75, null=True, blank=True, help_text=help['name'])
    race = models.ForeignKey(Race, null=True, blank=True, help_text=help['race'])
    gender = models.CharField(max_length=1, null=True, blank=True, choices=GENDER_CHOICES)
    age = models.PositiveIntegerField(null=True, blank=True, help_text=help['age'])

    @property
    def pretty_name(self):
        """
        Convienence method to return a descriptive string for the person
        """
        if self.name:
            return u'%s' % self.name
        if not self.name and self.race and self.gender:
            return u'Unknown %s %s' % (self.race, self.get_gender_display())
        return u'Unknown Person'

    # String Methods
    def __unicode__(self):
        if not self.name:
            return self.pretty_name
        return u'%s' % self.name
    def __str__(self):
        return smart_str(self.__unicode__())

    class Meta:
        verbose_name_plural = "people"

class Alias(models.Model):
    """
    Alternative names or aliases used by people.
    PC-ACE Model:  Victim partial
    """
    help = {
        'name': "Other or alternative name used.",
        'person': "Person the alias applies to"
    }
    name = models.CharField(max_length=75, help_text=help['name'])
    person = models.ForeignKey(Person, help_text=help['person'])

    # String Methods
    def __unicode__(self):
        return u'%s' % self.name
    def __str__(self):
        return smart_str(self.__unicode__())

class Lynching(models.Model):
    """
    Represents an invididual lynchning.
    PC-ACE Complex Object:  Victim (partial data used) see Person for more
    """
    help = {
        "pcaid": "Row number for victim complex object in PC-ACE",
        "pcalastupdate": "Datetime of last update form PC-Ace Data.",
        'county': "Most reliable county of the lynching.",
        'date': "Most reliable date of lynching.",
        'victim': "Person who was Lynched.",
        'crime': "Crime the victim was accused of.",
        'story': "The overarching event this is associated with."
        }

    pca_id = models.PositiveIntegerField(help_text=help["pcaid"], unique=True, db_index=True, editable=False)
    pca_last_update = models.DateTimeField(null=True, blank=True, editable=False, help_text=help["pcalastupdate"])
    county = models.ForeignKey(County, null=True, blank=True, help_text=help["county"])
    alternate_counties = models.ManyToManyField(County, related_name="alt_counties", null=True, blank=True) # List alternate possible counties here.
    date = models.DateField(null=True, blank=True, help_text=help["date"])
    victim = models.OneToOneField(Person, help_text=help["victim"])
    alleged_crime = models.ForeignKey(Accusation, null=True, blank=True, help_text=help['crime'])
    story = models.ForeignKey(Story, help_text=help['story'])

    # String Methods
    def __unicode__(self):
        return u'%s' % self.victim.name
    def __str__(self):
        return smart_str(self.__unicode__())

    class Meta:
        ordering = ['date',]

