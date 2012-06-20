from django.contrib import admin
from georgia_lynchings.articles.models import Article

class ArticleAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Standard Information', {
            'fields': (('title', 'featured'), 'creator', ('publisher', 'date', 'coverage',),
                       'rights', ('identifier', 'relation',), 'file'),
        }),
        ('Optional Information', {
            'classes': ('collapse',),
            'fields': ('subject','description','contributor', 'type', 'format',
                       'source', 'language'),
        }),
    )
    list_display = ('id', 'title', 'publisher', 'date', 'file') # id used since all others are not required
    #list_filter = ('publisher')
admin.site.register(Article, ArticleAdmin)