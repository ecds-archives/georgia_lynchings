'''
Common utility methods used elsewhere in the site.

'''

import httplib2
from django.conf import settings
import sunburnt

def solr_interface():
    http_opts = {}
    http = httplib2.Http(**http_opts)
    solr = sunburnt.SolrInterface(settings.SOLR_INDEX_URL,
                                  http_connection=http)
    return solr
