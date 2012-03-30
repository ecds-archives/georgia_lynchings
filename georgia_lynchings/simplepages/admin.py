from django.contrib import admin
from georgia_lynchings.simplepages.models import Page

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

admin.site.register(Page, PageAdmin)