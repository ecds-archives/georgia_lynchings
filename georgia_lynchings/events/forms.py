from django import forms
from django.conf import settings
import sunburnt

class SearchForm(forms.Form):
    q = forms.CharField()


def _choices_for_facet(field_name):
    '''Use a solr facet search to get choices for a ChoiceField.'''

    solr = sunburnt.SolrInterface(settings.SOLR_INDEX_URL)
    query = solr.query() \
                .facet_by(field_name) \
                .paginate(rows=0)
    facets = query.execute().facet_counts.facet_fields[field_name]
    # facet_fields returns a list of (facet, count). options takes
    # (id, label).
    choices = [('', '')] + \
              [(facet, '%s (%d)' % (facet, count))
               for (facet, count) in facets]
    return choices

class AdvancedSearchForm(forms.Form):
    participant = forms.CharField(required=False)
    victims = forms.CharField(required=False)
    locations = forms.CharField(required=False)
    alleged_crime = forms.ChoiceField(required=False, 
            choices=_choices_for_facet('victim_allegedcrime_brundage_facet'))
    all_text = forms.CharField(required=False)
