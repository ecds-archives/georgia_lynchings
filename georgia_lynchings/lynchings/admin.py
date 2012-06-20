from django.contrib import admin


from georgia_lynchings.articles.models import Article
from georgia_lynchings.lynchings.models import Race, Accusation, \
    Alias, Person, Lynching, Story


class RaceAdmin(admin.ModelAdmin):
    pass

class AccusationAdmin(admin.ModelAdmin):
    pass

class AliasInline(admin.TabularInline):
    model = Alias

class PersonAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Personal Attributes', {
            'fields': ('name', ('race', 'gender', 'age'),),
        }),
        ('PC-ACE Attributes', {
            'classes': ('collapse',),
            'fields': ('pca_id', 'pca_last_update'),
        }),
    )
    readonly_fields = ('pca_id', 'pca_last_update',) # avoids form error from including in fieldset above
    inlines = [
        AliasInline,
    ]

class LynchingAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Event Details', {
            'fields': ('victim', ('county', 'date'), 'alleged_crime', 'alternate_counties', 'story', ),
            }),
        ('PC-ACE Attributes', {
            'classes': ('collapse',),
            'fields': ('pca_id', 'pca_last_update')
        }),
        )
    readonly_fields = ('pca_id', 'pca_last_update',) # avoids form error from including in fieldset above
    filter_horizontal = ('alternate_counties',)
    list_display = ('victim', 'date', 'county')
    list_filter = ('county',)

class StoryAdmin(admin.ModelAdmin):
    filter_horizontal = ('articles',)

admin.site.register(Race, RaceAdmin)
admin.site.register(Accusation, AccusationAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Lynching, LynchingAdmin)
admin.site.register(Story, StoryAdmin)