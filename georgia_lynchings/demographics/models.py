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
    Census data from particular counties in particular years.
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
        return u'%s Census for %s County' % (self.year, self.county)
    def __str__(self):
        return smart_str(self.__unicode__())

    class Meta:
        ordering = ["county__name", "year"]

    @classmethod
    def statewide_totals_for_year(cls, year):
        fields = ['total', 'white', 'black', 'iltr_white', 'iltr_black']
        totals = cls.objects.filter(year=year).aggregate(
                **dict([(f, models.Sum(f)) for f in fields]))
        return cls(**totals)

    def statewide_totals(self):
        return self.statewide_totals_for_year(self.year)

    @property
    def literate_white(self):
        if self.white is not None and self.iltr_white is not None:
            return self.white - self.iltr_white

    @property
    def literate_black(self):
        if self.black is not None and self.iltr_black is not None:
            return self.black - self.iltr_black

    @property
    def percent_white(self):
        if self.white is not None and self.total:
            return float(self.white) / float(self.total) * 100.0

    @property
    def percent_black(self):
        if self.black is not None and self.total:
            return float(self.black) / float(self.total) * 100.0

    @property
    def white_percent_literate(self):
        if self.literate_white is not None and self.white:
            return float(self.literate_white) / float(self.white) * 100.0

    @property
    def black_percent_literate(self):
        if self.literate_black is not None and self.black:
            return float(self.literate_black) / float(self.black) * 100.0
