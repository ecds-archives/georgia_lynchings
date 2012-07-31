from django.db import models
from django.utils.encoding import smart_str

from georgia_lynchings.articles.models import Article
from georgia_lynchings.demographics.models import County

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

    @models.permalink
    def get_absolute_url(self):
        return ('lynchings:story_detail', [self.id])

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

class Lynching(models.Model):
    """
    Class to represent a connected sequence of events for an overall lynching.
    
    """
    help = {
        'pcaid': "Row number for Macro Event complex object in PC-ACE",
        'pcalastupdate': "Datetime of the last sync with PC-Ace Data.",
    }
    pca_id = models.PositiveIntegerField(help_text=help['pcaid'], unique=True, db_index=True)
    pca_last_update = models.DateTimeField(null=True, blank=True, editable=False, help_text=help["pcalastupdate"])

    articles = models.ManyToManyField(Article, help_text="Related Documents and Files")

    @models.permalink
    def get_absolute_url(self):
        return ('lynchings:lynching_detail', [self.id])

    @property
    def pretty_string(self):
        """
        Returns a more descriptive string for the story.
        """
        string_parts = [u'Lynching of',]
        string_parts.append(u", ".join([u"%s" % victim for victim in self.victim_set.all()]))
        date_set = set([u"%s" % victim.date.year for victim in self.victim_set.all() if victim.date])
        if date_set:
            string_parts.append(u"in %s" % ", ".join(date_set))
        return u" ".join(string_parts)

    @property
    def county_list(self):
        """
        Convienence method to generate a list of all counties.
        """
        return list(set([victim.county for victim in self.victim_seta.all()]))

    @property
    def year(self):
        """
        Best determination of date of lynching.
        """
        year_list = sorted([victim.date.year for victim in self.victim_set.all() if victim.date])
        if year_list:
            return year_list[-1] # return the highest date
        return None

    # String Methods
    def __unicode__(self):
        return u'%s' % self.pretty_string
    def __str__(self):
        return smart_str(self.__unicode__())

class Victim(models.Model):
    """
    Represents an individual person who was lynched and the details of that attack.

    NOTE:  The corrisponding row headers are added as comments after each field.
    """
    help = {
        'lynching': 'Lynching this victim is associated with.',
        'name': 'Full name of victim.',
        'race': 'Race.',
        'sex': 'Gender.',
        'date': 'Date of Lynching.',
        'detailed_reason': '',
        'accusation': '', # many to many
        'county': 'County of Lynching',
    }
    lynching = models.ForeignKey(Lynching, help_text=help['lynching'], null=True, blank=True) # ID Macro Event
    name = models.CharField(max_length=75, help_text=help['name'], null=True, blank=True) # Name of Victim (Beck)
    race = models.ForeignKey(Race, null=True, blank=True) # Race (Beck)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True) # Sex (Beck)
    date = models.DateField(help_text=help['date'], null=True, blank=True) # Lynching date (Beck)
    detailed_reason = models.TextField(help_text=help['detailed_reason'], null=True, blank=True) # Reason (Beck)
    accusation = models.ManyToManyField(Accusation, null=True, blank=True) # Reason Aggregate Code 1
    county = models.ForeignKey(County, null=True, blank=True) # County of Lynching (Beck)

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