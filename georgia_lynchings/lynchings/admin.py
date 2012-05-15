from django.contrib import admin

from georgia_lynchings.lynchings.models import County, Race, Accusation

class CountyAdmin(admin.ModelAdmin):
    pass

class RaceAdmin(admin.ModelAdmin):
    pass

class AccusationAdmin(admin.ModelAdmin):
    pass

class PersonAdmin(admin.ModelAdmin):
    pass

admin.site.register(County, CountyAdmin)
admin.site.register(Race, RaceAdmin)
admin.site.register(Accusation, AccusationAdmin)