import logging

from django.db import models
from django.conf import settings

from georgia_lynchings.rdf.fields import ChainedRdfPropertyField, \
        ReversedRdfPropertyField, RdfPropertyField
from georgia_lynchings.rdf.models import RdfObject, ComplexObject
from georgia_lynchings.rdf.ns import dd, dxcxd, ssxn

logger = logging.getLogger(__name__)

# DC fields as follows NOTE: remove theses
#Title  - Title of Article
#Creator  - Author's name (list multiple here if applicable)
#Subject - Probably blank
#Description - Description information or additional notes
#Publisher - Name of Newspaper
#Contributor  - Probably blank
#Date  - Date story published
#Type  - 'News Article' by default in case we add other kinds of information later.
#Format  - Blank probably.
#Identifier  - Blank probably but if we have DOIs later we can use that.
#Source  - Name of archival source
#Language - 'en' by default
#Relation - Probably blank
#Coverage - probably blank
#Rights  - Text field, use however you like.
NEWS_TYPE = 'NA'
ENGLISH_TYPE = 'EN'
ARTICLE_TYPES = (
    (NEWS_TYPE, 'News Article'),
)
LANGUAGE_TYPES = (
    (ENGLISH_TYPE, 'English'),
)

class Article(models.Model):
    """
    A model to represent a primary source PDF article about a lynching event.
    """
    help = {
        'title': 'Title of news article.',
        'creator': 'Article Author name(s), seperate by colon if multiple.',
        'subject': '',
        'description':  'Description about the article itself.',
        'publisher': 'Title of the newspaper article was published in.',
        'contributor': '',
        'date': 'Date story was published.',
        'type': 'The type of article.',
        'format': '',
        'identifier': 'URI used for document in the RDF',
        'source': 'Source or archive the article was obtained from if known.',
        'language': 'Language article was written in.',
        'relation': 'URI of event this article references.',
        'coverage': 'Page number(s) of the article if known.',
        'rights': 'Rights information to display about the article.',
    }
    # Standard Dublin Core Fields
    title = models.CharField(max_length=255, help_text=help['title'], null=True, blank=True)
    creator = models.CharField(max_length=255, help_text=help['creator'], null=True, blank=True)
    subject = models.CharField(max_length=100, help_text=help['subject'], null=True, blank=True)
    description = models.TextField(help_text=help['description'], null=True, blank=True)
    publisher = models.CharField(max_length=100, help_text=help['publisher'], null=True, blank=True)
    contributor = models.CharField(max_length=255, help_text=help['contributor'], null=True, blank=True)
    date = models.DateField(help_text=help['date'], null=True, blank=True)
    type = models.CharField(max_length=2, choices=ARTICLE_TYPES, default=NEWS_TYPE, help_text=help['type'])
    format = models.CharField(max_length=100, help_text=help['format'], null=True, blank=True)
    identifier = models.CharField(max_length=100, help_text=help['identifier'], null=True, blank=True)
    source = models.CharField(max_length=100, help_text=help['source'], null=True, blank=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_TYPES, default=ENGLISH_TYPE, help_text=help['language'])
    relation = models.CharField(max_length=100, help_text=help['relation'], null=True, blank=True)
    coverage = models.CharField(max_length=25, help_text=help['coverage'], null=True, blank=True)
    rights = models.TextField(help_text=help['rights'], null=True, blank=True)

    # Fields dealing with File objects and their permissions.
    file_help = "PDF file representing the article.  DO NOT UPLOAD FILES WE DO NOT HAVE THE RIGHTS TO USE."
    file = models.FileField(upload_to=settings.ARTICLE_UPLOAD_DIR, help_text=file_help, null=True, blank=True)

    def __unicode__(self):
        return u"%s" % (self.title)

class PcAceDocument(RdfObject):
    """
    A PDF document in PC-ACE, with metadata in the RDF triplestore.
    """

    rdf_type = dd.Row
    'the URI of the RDF Class describing document objects'

    id = dd.ID
    'the numeric id used in PC-ACE for the document'

    newspaper_name = ssxn.Newspaper_name
    'the name of the newspaper the document comes from'
    newspaper_date = ssxn.Newspaper_date
    'the date of the newspaper the document comes from'
    page_number = ssxn.Page_number
    'the page number of the document'

    _pdf_path = ssxn.documentPath
    '''the relative path to the document. assumes windows path conventions and
       a predefined directory structure'''

    documented = ChainedRdfPropertyField(
            ReversedRdfPropertyField(dxcxd.Document),
            RdfPropertyField(dxcxd.Complex,
                result_type=ComplexObject, multiple=True),
            reverse_field_name='documents',
        )
    '''the list of :class:`~georgia_lynchings.rdf.models.ComplexObject`
    objects associated with this document. In practice, this property is
    more useful in reverse: It creates a ``documents`` property on
    :class:`~georgia_lynchings.rdf.models.ComplexObject` that lists all of
    the :class:`PcAceDocument` objects associated with that object.'''

    @property
    def pdf_filename(self):
        'the document filename, stripped of OS and directory structure'
        fpath = self._pdf_path
        if fpath:
            path, bslash, fname = fpath.rpartition('\\')
            return fname
