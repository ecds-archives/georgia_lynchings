from mock import Mock, MagicMock
from sunburnt import sunburnt

    # solr interface has a fluent interface where queries and filters
    # return another solr query object; simulate that as simply as possible
    # mocksolr.query.return_value = mocksolr.query
    # mocksolr.query.return_value = mocksolr.query
    # mocksolr.query.query.return_value = mocksolr.query
    # mocksolr.query.filter.return_value = mocksolr.query
    # mocksolr.query.paginate.return_value = mocksolr.query
    # mocksolr.query.exclude.return_value = mocksolr.query
    # mocksolr.query.sort_by.return_value = mocksolr.query
    # mocksolr.query.facet_by.return_value = mocksolr.query
    # mocksolr.query.field_limit.return_value = mocksolr.query
    # mocksolr.query.highlight.return_value = mocksolr.query
mocksolr = MagicMock(sunburnt.SolrInterface)
mocksolr.return_value = mocksolr
mocksolr.query.return_value = mocksolr.query
for method in ['query', 'filter', 'paginate', 'exclude', 'sort_by', 'facet_by',
               'field_limit', 'highlight']:
    getattr(mocksolr.query, method).return_value = mocksolr.query
