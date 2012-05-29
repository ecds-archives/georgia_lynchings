from django.contrib import admin

from georgia_lynchings.demographics.models import County, Population

class PopulationInline(admin.TabularInline):
    model = Population

class CountyAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')
    inlines = [PopulationInline,]

class PopulationAdmin(admin.ModelAdmin):
    list_display = ('county', 'total', 'white', 'black',
                    'iltr_white', 'iltr_black', 'year')
    list_filter = ('year', 'county')

admin.site.register(County, CountyAdmin)
admin.site.register(Population, PopulationAdmin)