from django.contrib import admin


from georgia_lynchings.articles.models import Article
from georgia_lynchings.lynchings.models import Race, Accusation, Lynching, Story, Victim


class RaceAdmin(admin.ModelAdmin):
    pass

class AccusationAdmin(admin.ModelAdmin):
    pass

class StoryAdmin(admin.ModelAdmin):
    filter_horizontal = ('articles',)

class LynchingAdmin(admin.ModelAdmin):
    pass

class VictimAdmin(admin.ModelAdmin):
    list_filter = ('county',)

admin.site.register(Race, RaceAdmin)
admin.site.register(Accusation, AccusationAdmin)
admin.site.register(Lynching, LynchingAdmin)
admin.site.register(Victim, VictimAdmin)