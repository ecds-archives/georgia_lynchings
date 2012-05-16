from django.contrib import admin

from georgia_lynchings.lynchings.models import County, Race, Accusation, \
    Alias, Person, Lynching

class CountyAdmin(admin.ModelAdmin):
    pass

class RaceAdmin(admin.ModelAdmin):
    pass

class AccusationAdmin(admin.ModelAdmin):
    pass

class AliasInline(admin.TabularInline):
    model = Alias

class PersonAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Personal Attributes', {
            'fields': ('name', ('race', 'gender', 'age')),
        }),
        ('PC-ACE Attributes', {
            'classes': ('collapse',),
            'fields': ('pca_id',)
        }),
    )
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
            'fields': ('pca_id',)
        }),
        )
    filter_horizontal = ('alternate_counties',)

admin.site.register(County, CountyAdmin)
admin.site.register(Race, RaceAdmin)
admin.site.register(Accusation, AccusationAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Lynching, LynchingAdmin)