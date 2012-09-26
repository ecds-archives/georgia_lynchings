from django.contrib import admin
from django.conf import settings
from django.db import models
from django import forms

from georgia_lynchings.simplepages.models import Page

static_url = settings.STATIC_URL

class PageAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Page', {
            'fields': ('title', 'content'),
            }),
        ('Other Information', {
            'classes': ('collapse',),
            'fields': ('slug',),
            }),
        )
    prepopulated_fields = {"slug": ("title",)}
    list_display = ('title', 'date_created') # id used since all others are not required
    # So TinyMCE works
    formfield_overrides = { models.TextField: {'widget': forms.Textarea(attrs={'class':'tinymce'})}, }

    class Media:
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js',
            ''.join([static_url, 'js/tinymce/jscripts/tiny_mce/jquery.tinymce.js']),
            ) # Note this works with code in templates/admin/base_site.html 

admin.site.register(Page, PageAdmin)