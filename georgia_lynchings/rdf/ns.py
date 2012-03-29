from django.conf import settings
from rdflib import Namespace

def _source_file_ns(fname, id_prefix=''):
    uri = '%ssource_data_files/%s#%s' % (settings.APPLICATION_RDF_NS_ROOT,
                                         fname, id_prefix)
    return Namespace(uri)

def _constructed_stmts_ns(construct_stmt_path, id_prefix=''):
    uri = '%sconstructed_statements/index/%s/#%s' % (settings.APPLICATION_RDF_NS_ROOT,
                                         construct_stmt_path, id_prefix)                                         
    return Namespace(uri)

# NOTE: RDF namespaces for this project are derived by project scripts from
# PC-ACE database tables. Each CSV file here is a table in the source
# database. These table-base namespaces are shared by all PC-ACE databases
# (perhaps differing by PC-ACE version), so if we end up splitting general
# PC-ACE functionality from project-specific functionality then these
# namespaces are probably reusable.

dcx = _source_file_ns('data_Complex.csv')
dd = _source_file_ns('data_Document.csv')
dsxd = _source_file_ns('data_SimplexDate.csv')
dsxn = _source_file_ns('data_SimplexNumber.csv')
dsxt = _source_file_ns('data_SimplexText.csv')
dsx = _source_file_ns('data_Simplex.csv')
dttcu = _source_file_ns('data_TempTranslatorCU.csv')
dvcta = _source_file_ns('data_VCommentArchive.csv')
dxacxcx = _source_file_ns('data_xref_AnyComplex-Complex.csv')
dxctcx = _source_file_ns('data_xref_comment-complex.csv')
dxctd = _source_file_ns('data_xref_Comment-Document.csv')
dxctsx = _source_file_ns('data_xref_Comment-Simplex.csv')
dxcxcx = _source_file_ns('data_xref_Complex-Complex.csv')
dxcxd = _source_file_ns('data_xref_Complex-Document.csv')
dxsxcx = _source_file_ns('data_xref_Simplex-Complex.csv')
dxsxd = _source_file_ns('data_xref_Simplex-Document.csv')
dxsxsxd = _source_file_ns('data_xref_Simplex-Simplex-Document.csv')
dxvctd = _source_file_ns('data_xref_VComment-Document.csv')
dxvct = _source_file_ns('data_xref_VComment.csv')
scx = _source_file_ns('setup_Complex.csv')
scxn = _source_file_ns('setup_Complex.csv', id_prefix='name-')
sd = _source_file_ns('setup_Document.csv')
ssx = _source_file_ns('setup_Simplex.csv')
ssxn = _source_file_ns('setup_Simplex.csv', id_prefix='name-')
sxcxcx = _source_file_ns('setup_xref_Complex-Complex.csv')
sxcxcxn = _source_file_ns('setup_xref_Complex-Complex.csv', id_prefix='name-')
sxsxcx = _source_file_ns('setup_xref_Simplex-Complex.csv')
sxsxd = _source_file_ns('setup_xref_Simplex-Document.csv')

ix_ebd = _constructed_stmts_ns('events_by_date')
