from django.db import models
from django.utils.encoding import smart_str

YEAR_CHOICES = (
    (1870, 1870),
    (1880, 1880),
    (1890, 1890),
    (1900, 1900),
    (1910, 1910),
    (1920, 1920),
    (1930, 1930),
)

class County(models.Model):
    """
    Represents data about a particular county.
    """
    name = models.CharField(max_length=50, help_text="Name of County")
    latitude = models.FloatField(null=True, blank=True, help_text="Latitude for geographic center of county.")
    longitude = models.FloatField(null=True, blank=True, help_text="Longitude for geographic center of county.")

    # String Methods
    def __unicode__(self):
        return u'%s' % self.name
    def __str__(self):
        return smart_str(self.__unicode__())

    class Meta:
        verbose_name_plural = "counties"
        ordering = ["name"]

class Population(models.Model):
    """
    Cencus data from particular counties in particular years.
    """
    county = models.ForeignKey(County, help_text="County that data is for.")
    year = models.PositiveIntegerField(choices=YEAR_CHOICES,
        help_text="Year of Census data.")
    total = models.PositiveIntegerField(null=True, blank=True,
        help_text="Total Population.")
    white = models.PositiveIntegerField(null=True, blank=True,
        help_text="White Population.")
    black = models.PositiveIntegerField(null=True, blank=True,
        help_text="Black Population.")
    iltr_white = models.PositiveIntegerField(null=True, blank=True,
        help_text="Illiterate White Population.")
    iltr_black = models.PositiveIntegerField(null=True, blank=True,
        help_text="Illiterate Black Population.")

    # String Methods
    def __unicode__(self):
        return u'%s Cencus for %s County' % (self.year, self.county)
    def __str__(self):
        return smart_str(self.__unicode__())

    class Meta:
        ordering = ["county__name", "year"]
