from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

class Page(models.Model):
    """
    Basic class to manage and display basic web content.
    """
    title = models.CharField(max_length=50,  help_text='Page Title')
    slug = models.SlugField(max_length=50, help_text="slug text to use in url")
    content = models.TextField(null=True, blank=True, help_text="Page Body")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('simple page')
        verbose_name_plural = _('simple pages')
        ordering = ('title',)

    def __unicode__(self):
        return u"%s" % self.title

    @models.permalink
    def get_absolute_url(self):
        return ('view_page', (), {
            'slug': self.slug,
        })
