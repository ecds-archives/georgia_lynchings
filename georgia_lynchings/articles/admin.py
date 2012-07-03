from django.contrib import admin
from georgia_lynchings.articles.models import Article

class ArticleAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Standard Information', {
            'fields': (('title', 'featured'), 'creator', ('publisher', 'date', 'coverage',),
                'description', 'rights', ('identifier', 'relation',), 'source', 'file'),
        }),
        ('Optional Information', {
            'classes': ('collapse',),
            'fields': ('subject','contributor', 'type', 'format',
                       'language'),
        }),
    )
    list_display = ('id', 'title', 'publisher', 'date', 'file') # id used since all others are not required
    #list_filter = ('publisher')
admin.site.register(Article, ArticleAdmin)