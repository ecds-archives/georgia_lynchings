from django.contrib import admin

from georgia_lynchings.reldata.models import Relationship

class RelationshipAdmin(admin.ModelAdmin):
    list_display = ('subject_desc', 'subject_adjective', 'process_reason', 'process_instrument')

admin.site.register(Relationship, RelationshipAdmin)


