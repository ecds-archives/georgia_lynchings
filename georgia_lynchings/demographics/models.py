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
    latitude = models.FloatField()
    longitude = models.FloatField()

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
    county = models.ForignKey(County, help_text="County that data is for.")
    year = models.PositiveInteger(choices=YEAR_CHOICES,
        help_text="Year of Census data.")
    total = models.PositiveInteger(null=True, blank=True,
        help_text="Total Population.")
    white = models.PositiveInteger(null=True, blank=True,
        null=True, blank=True,
        help_text="White Population.")
    black = models.PositiveInteger(null=True, blank=True,
        help_text="Black Population.")
    iltr_white = models.PositiveInteger(null=True, blank=True,
        help_text="Illiterate White Population.")
    iltr_black = models.PositiveInteger(null=True, blank=True,
        help_text="Illiterate Black Population.")
