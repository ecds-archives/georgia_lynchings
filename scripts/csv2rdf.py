#!/usr/bin/env python

'''Convert project CSV files to RDF.

Usage: csv2rdf.py file.csv ...

Another script, mdb2csv.sh, exports Georgia Lynchings data from a PC-ACE MS
Access relational database to CSV files. csv2rdf.py converts those CSV files
to RDF. It uses the name of the file to determine how to interpret the data
in the file, and it outputs the converted data as a .ttl (turtle RDF) file
next to its respective .csv input file. Unrecognized fields and files are
translated as simple string properties.

The strategy of the script is to read the header line of the file to get
field names, and to interpret those field names as RDF property names. For
each row of the source CSV file, the script creates a Row object with a URI
based on the row's ID. It then outputs an RDF statement for each column,
translating the value according to file-specific and column-specific code in
the script. The URIs of the Row class, all properties, and all individual
Row objects are defined here within a namespace derived from the source
file's name.
'''

import csv
import datetime
import os
import re
import sys
import urllib

URI_BASE = 'http://galyn.example.com/source_data_files/'
'''The base URI for the source files we're creating. This is defined in
several places across the project and will need to change in all of them
when this base changes to its more permanent URI.'''

def uri_from_path(fpath, base=None):
    '''Given a path, pull out the file name and return an absolute URI for
    that file name in the project base URI.'''
    if base is None:
        base = URI_BASE
    dirname, fname = os.path.split(fpath)
    return base + fname

class Converter(object):
    '''Base class for file-specific CSV to RDF converters. This class
    contains the basic shared logic for reading a CSV file and outputting
    its information as RDF, relying on subclasses for translating individual
    fields.

    By default, all fields are translated to RDF string literals. To
    override this, subclasses should define an encode_<fieldname> method.
    The Converter will call that method, passing the source data. The method
    should return a Python string containing the TTL-encoded value, exactly
    as it should appear in the output file. Alternately, the method may
    return ``None`` to indicate that the property should not be created on
    this object.
    '''

    def process_file(self, in_fname):
        'Process a single CSV file into turtle (TTL) RDF.'
        self.in_uri = uri_from_path(in_fname)
        out_fname = self.make_output_filename(in_fname)
        with open(in_fname) as inf, open(out_fname, 'w') as outf:
            reader = csv.reader(inf)
            row_iter = iter(reader)
            columns = row_iter.next()
            
            print >>outf, '@base <%s> .' % (self.in_uri,)
            self.output_prefixes(outf)

            for row in row_iter:
                self.process_row(outf, row, columns)

    def make_output_filename(self, in_fname):
        '''Generate an output filename from an input filename, adding
        numeric suffixes to make sure the output file doesn't overwrite any
        files already present in the filesystem.'''
        in_base, ext = os.path.splitext(in_fname)
        out_ext = '.ttl'
        out_fname = in_base + out_ext
        i = 0
        while os.path.exists(out_fname):
            i += 1
            out_fname = '%s.%d%s' % (in_base, i, out_ext)
        return out_fname

    def output_prefixes(self, outf):
        '''Empty hook for subclasses to outuput necessary TTL @prefix
        statements at the beginning of the output file. Subclasses that use
        RDF namespaces in their output should override this function to
        define those prefixes.'''
        pass

    def process_row(self, outf, row, columns):
        # row[0] is always ID
        print >>outf, '<#r%s> a <#Row>' % (row[0],),
        for prop, val in zip(columns, row):
            output = getattr(self, 'output_' + prop, self.output_property)
            output(outf, prop, val)
        print >>outf, '.'

    def output_property(self, outf, prop, val):
        encode = getattr(self, 'encode_' + prop, self.encode)
        encoded = encode(val)
        if encoded is not None:
            print >>outf, ';\n   <#%s> %s' % (prop, encoded),

    NORMALIZE_NAME = re.compile('[^_A-Za-z0-9]+')
    def normalize_name_for_uri(self, name):
        # remove apostrophes so that "foo's" becomes "foos" instead of "foo_s"
        name = name.replace("'", "")
        # replace any nonalphanumeric characters with _, collapsing any
        # repeating __ into a single _
        name = self.NORMALIZE_NAME.sub('_', name)
        # strip off any leading or trailing _
        name = name.strip('_')
        return name
    
    def encode(self, val):
        '''Default TTL encoder for field values. By default, output field
        values as RDF string literals.'''
        # lacking other info, assume string
        return self._encode_as_string(val)

    def _encode_as_string(self, val):
        '''Utility method for Converters: Quote a value for output in TTL as
        an RDF string literal.'''
        val = val.replace('\\', '\\\\') \
                 .replace('"', '\"')
        if '\n' in val:
            return '"""%s"""' % (val,)
        else:
            return '"%s"' % (val,)

    def _encode_as_decimal(self, val):
        '''Utility method for Converters: Quote a value for output in TTL as
        an RDF decimal literal. Returns ``None`` (no property value) if the
        input value is empty.

        NOTE: Subclasses using this method must override
        :meth:`output_prefixes` to define the ``xsd`` prefix.
        '''
        if val:
            return '"%s"^^xsd:decimal' % (val,)

    def _encode_as_integer(self, val):
        '''Utility method for Converters: Quote a value for output in TTL as
        an RDF integer literal. Returns ``None`` (no property value) if the
        input value is empty.

        NOTE: Subclasses using this method must override
        :meth:`output_prefixes` to define the ``xsd`` prefix.
        '''
        if val:
            return '"%s"^^xsd:integer' % (val,)

    def _encode_as_boolean(self, val):
        '''Utility method for Converters: Quote a value for output in TTL as
        an RDF boolean literal. Returns ``None`` (no property value) if the
        input value is empty.

        NOTE: Subclasses using this method must override
        :meth:`output_prefixes` to define the ``xsd`` prefix.
        '''
        if val:
            xsdval = 'false' if val == '0' else 'true'
            return '"%s"^^xsd:boolean' % (xsdval,)


class Converter_data_Complex(Converter):
    ''':class:`Converter` subclass for ``data_Complex.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix scx: <setup_Complex.csv#> .'

    def encode_ComplexType(self, val):
        return 'scx:r' + val


class Converter_data_Document(Converter):
    ''':class:`Converter` subclass for ``data_Document.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_Document, self).output_prefixes(outf)
        print >>outf, '@prefix sd: <setup_Document.csv#> .'

    def encode_DocumentType(self, val):
        return 'sd:r' + val


class Converter_data_Simplex(Converter):
    ''':class:`Converter` subclass for ``data_Simplex.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_Simplex, self).output_prefixes(outf)
        print >>outf, '@prefix ssx: <setup_Simplex.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_SimplexType(self, val):
        return 'ssx:r' + val

    # Note: refValue is an index into data_Simplex*. Lookup table selection
    # depends on simplexType.ValueType. 1==Text; 2==Number; 3==Date. 4
    # indicates that refValue directly encodes boolean data. This kind of
    # processing is well beyond the scope of this script, so here we use the
    # default string encoding and match up the value later in
    # scripts/add-inferred-statements.{sh,rq}

    def encode_Locked(self, val):
        return self._encode_as_boolean(val)


class Converter_data_SimplexDate(Converter):
    ''':class:`Converter` subclass for ``data_SimplexDate.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_SimplexDate, self).output_prefixes(outf)
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_Value(self, val):
        dtval = datetime.datetime.strptime(val, '%m/%d/%y %H:%M:%S')
        dtval = dtval.replace(year=dtval.year - 100)
        return '"%s"^^xsd:dateTime' % (dtval.isoformat(),)
        

class Converter_data_SimplexNumber(Converter):
    ''':class:`Converter` subclass for ``data_SimplexNumber.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_SimplexNumber, self).output_prefixes(outf)
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_Value(self, val):
        return self._encode_as_decimal(val)


class Converter_data_SimplexText(Converter):
    ''':class:`Converter` subclass for ``data_SimplexText.csv``'''
    pass # nothing to do?


class Converter_data_VCommentArchive(Converter):
    ''':class:`Converter` subclass for ``data_VCommentArchive.csv``'''
    pass

    # TODO: What are UserID/VerifierID?

    # TODO: Do we need to split up Position macro events?


class Converter_data_xref_AnyComplex_Complex(Converter):
    ''':class:`Converter` subclass for ``data_xref_AnyComplex-Complex.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_xref_AnyComplex_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix dcx: <data_Complex.csv#> .'

    def encode_Complex(self, val):
        return 'dcx:r' + val
        
    # TODO: What is AnyComplex?
    def encode_AnyComplex(self, val):
        if val:
            return self._encode_as_string(val)


class Converter_data_xref_comment_complex(Converter):
    ''':class:`Converter` subclass for ``data_xref_comment-complex.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_xref_comment_complex, self).output_prefixes(outf)
        print >>outf, '@prefix dcx: <data_Complex.csv#> .'

    def encode_Complex(self, val):
        return 'dcx:r' + val


class Converter_data_xref_Comment_Document(Converter):
    ''':class:`Converter` subclass for ``data_xref_Comment-Document.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_xref_Comment_Document, self).output_prefixes(outf)
        print >>outf, '@prefix dd: <data_Document.csv#> .'

    def encode_Document(self, val):
        return 'dd:r' + val


class Converter_data_xref_Comment_Simplex(Converter):
    ''':class:`Converter` subclass for ``data_xref_Comment-Simplex.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_xref_Comment_Simplex, self).output_prefixes(outf)
        print >>outf, '@prefix dsx: <data_Simplex.csv#> .'

    def encode_Simplex(self, val):
        return 'dsx:r' + val


class Converter_data_xref_Complex_Complex(Converter):
    ''':class:`Converter` subclass for ``data_xref_Complex-Complex.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_xref_Complex_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix dcx: <data_Complex.csv#> .'
        print >>outf, '@prefix sxcxcx: <setup_xref_Complex-Complex.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_HigherComplex(self, val):
        if val != '-1':
            return 'dcx:r' + val

    def encode_LowerComplex(self, val):
        if val != '-1':
            return 'dcx:r' + val

    def encode_xrefID(self, val):
        return 'sxcxcx:r' + val

    def encode_Order(self, val):
        return self._encode_as_integer(val)


class Converter_data_xref_Complex_Document(Converter):
    ''':class:`Converter` subclass for ``data_xref_Complex-Document.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_xref_Complex_Document, self).output_prefixes(outf)
        print >>outf, '@prefix dcx: <data_Complex.csv#> .'
        print >>outf, '@prefix dd: <data_Document.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_Complex(self, val):
        return 'dcx:r' + val

    def encode_Document(self, val):
        return 'dd:r' + val

    def encode_Complete(self, val):
        return self._encode_as_boolean(val)

    def encode_Verified(self, val):
        return self._encode_as_boolean(val)


class Converter_data_xref_Simplex_Complex(Converter):
    ''':class:`Converter` subclass for ``data_xref_Simplex-Complex.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_xref_Simplex_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix dcx: <data_Complex.csv#> .'
        print >>outf, '@prefix dsx: <data_Simplex.csv#> .'
        print >>outf, '@prefix sxsxcx: <setup_xref_Simplex-Complex.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_xrefID(self, val):
        return 'sxsxcx:r' + val

    def encode_Simplex(self, val):
        return 'dsx:r' + val

    def encode_Complex(self, val):
        return 'dcx:r' + val

    def encode_Order(self, val):
        return self._encode_as_integer(val)


class Converter_data_xref_Simplex_Document(Converter):
    ''':class:`Converter` subclass for ``data_xref_Simplex-Document.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_xref_Simplex_Document, self).output_prefixes(outf)
        print >>outf, '@prefix dxsxcx: <data_xref_Simplex-Complex.csv#> .'
        print >>outf, '@prefix dd: <data_Document.csv#> .'

    def encode_Simplex(self, val):
        return 'dxsxcx:r' + val

    def encode_Document(self, val):
        return 'dd:r' + val

class Converter_data_xref_Simplex_Simplex_Document(Converter):
    ''':class:`Converter` subclass for ``data_xref_Simplex-Simplex-Document.csv``'''
    def output_prefixes(self, outf):
        super(Converter_data_xref_Simplex_Simplex_Document, self).output_prefixes(outf)
        print >>outf, '@prefix dsx: <data_Simplex.csv#> .'
        print >>outf, '@prefix dd: <data_Document.csv#> .'
        print >>outf, '@prefix sxsxd: <setup_xref_Simplex-Document.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'
    
    def encode_xrefID(self, val):
        if val:
            return 'sxsxd:r' + val

    def encode_Simplex(self, val):
        if val:
            return 'dsx:r' + val

    def encode_Document(self, val):
        if val:
            return 'dd:r' + val

    def encode_Order(self, val):
        return self._encode_as_integer(val)


class Converter_data_xref_VComment(Converter):
    ''':class:`Converter` subclass for ``data_xref_VComment.csv``'''
    # TODO: this table is undocumented. many fields guessed or entirely unknown

    def output_prefixes(self, outf):
        super(Converter_data_xref_VComment, self).output_prefixes(outf)
        print >>outf, '@prefix dcx: <data_Complex.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_Complex(self, val):
        return 'dcx:r' + val

    def encode_Completed(self, val):
        return self._encode_as_boolean(val)


class Converter_data_xref_VComment_Document(Converter):
    ''':class:`Converter` subclass for ``data_xref_VComment-Document.csv``'''
    # TODO: this table is undocumented. many fields guessed or entirely unknown

    def output_prefixes(self, outf):
        super(Converter_data_xref_VComment_Document, self).output_prefixes(outf)
        print >>outf, '@prefix dcx: <data_Complex.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_Complex(self, val):
        return 'dcx:r' + val

    def encode_Completed(self, val):
        return self._encode_as_boolean(val)


class Converter_setup_Complex(Converter):
    ''':class:`Converter` subclass for ``setup_Complex.csv``'''
    # TODO: copySetting: Is this a boolean? number?
    # TODO: DocumentType: Does this reference setup_Document? maybe?

    def output_prefixes(self, outf):
        super(Converter_setup_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix scxn: <#name-> .'

    def output_Name(self, outf, prop, val):
        # do default property processing
        self.output_property(outf, prop, val)
        # and then also add an alternate spelling
        print >>outf, ';\n   <#Name-URI> scxn:%s' % \
                (self.normalize_name_for_uri(val),),


class Converter_setup_Document(Converter):
    ''':class:`Converter` subclass for ``setup_Document.csv``'''
    # DocumentType looks like just a string. Leave it for now.
    pass


class Converter_setup_Simplex(Converter):
    ''':class:`Converter` subclass for ``setup_Simplex.csv``'''
    def output_prefixes(self, outf):
        super(Converter_setup_Simplex, self).output_prefixes(outf)
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'
        print >>outf, '@prefix ssxn: <#name-> .'

    def output_Name(self, outf, prop, val):
        # do default property processing
        self.output_property(outf, prop, val)
        # and then also add an alternate spelling
        print >>outf, ';\n   <#Name-URI> ssxn:%s' % \
                (self.normalize_name_for_uri(val),),

    def encode_ValueType(self, val):
        # TODO: Find a more meaningful way to encode the actual meaning of
        # this number, and update add-inferred-statments to reflect this
        # change. For now we just echo the number from the source data:
        #   1. text (in data_SimplexText)
        #   2. number (in data_SimplexNumber)
        #   3. date (in data_SimplexDate)
        #   4. boolean, directly encoded
        #   5. time (in data_SimplexDate)
        return self._encode_as_integer(val)

    def encode_Locked(self, val):
        return self._encode_as_boolean(val)


class Converter_setup_xref_Complex_Complex(Converter):
    ''':class:`Converter` subclass for ``setup_xref_Complex-Complex.csv``'''
    def output_prefixes(self, outf):
        super(Converter_setup_xref_Complex_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix scx: <setup_Complex.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'
        print >>outf, '@prefix sxcxcxn: <#name-> .'

    def output_Name(self, outf, prop, val):
        # do default property processing
        self.output_property(outf, prop, val)
        # and then also add an alternate spelling
        print >>outf, ';\n   <#Name-URI> sxcxcxn:%s' % \
                (self.normalize_name_for_uri(val),),

    def encode_HigherComplex(self, val):
        if val != '-1':
            return 'scx:r' + val
        
    def encode_LowerComplex(self, val):
        if val != '-1':
            return 'scx:r' + val
        
    # TODO: What is Relationship?

    def encode_Order(self, val):
        return self._encode_as_integer(val)

    # TODO: What is Group?

    def encode_Required(self, val):
        return self._encode_as_boolean(val)

    def encode_AllowMultiple(self, val):
        return self._encode_as_boolean(val)
        
    # TODO: What is Autoxref?


class Converter_setup_xref_Simplex_Complex(Converter):
    ''':class:`Converter` subclass for ``setup_xref_Simplex-Complex.csv``'''
    def output_prefixes(self, outf):
        super(Converter_setup_xref_Simplex_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix scx: <setup_Complex.csv#> .'
        print >>outf, '@prefix ssx: <setup_Simplex.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_Complex(self, val):
        return 'scx:r' + val

    def encode_Simplex(self, val):
        return 'ssx:r' + val

    # TODO: What is Autoxref?
    # TODO: how do we interpret defaultVal?

    def encode_Order(self, val):
        return self._encode_as_integer(val)

    # TODO: What is Group?

    def encode_Required(self, val):
        return self._encode_as_boolean(val)

    def encode_AllowMultiple(self, val):
        return self._encode_as_boolean(val)
        

class Converter_setup_xref_Simplex_Document(Converter):
    ''':class:`Converter` subclass for ``setup_xref_Simplex-Document.csv``'''
    def output_prefixes(self, outf):
        super(Converter_setup_xref_Simplex_Document, self).output_prefixes(outf)
        print >>outf, '@prefix sd: <setup_Document.csv#> .'
        print >>outf, '@prefix ssx: <setup_Simplex.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_Document(self, val):
        return 'sd:r' + val

    def encode_Simplex(self, val):
        return 'ssx:r' + val

    # TODO: how do we interpret defaultVal?

    def encode_Required(self, val):
        return self._encode_as_boolean(val)

    def encode_AllowMultiple(self, val):
        return self._encode_as_boolean(val)
    
    def encode_Order(self, val):
        return self._encode_as_integer(val)

    # TODO: What is Group?


def converter_for_filename(fname):
    '''Look up the file-specific :class:`Converter` for a file based on its
    filename. Look for a class named ``Converter_<filename>``, withe the
    file extension stripped and dashes changed to underscores.
    '''
    basename, ext = os.path.splitext(fname)
    converter_name = 'Converter_' + basename.replace('-', '_')
    return globals().get(converter_name, Converter)

def convert_file(fname):
    '''Convert a single file by name, using the appropriate
    :class:`Converter` according to the filename.'''
    dirpart, filepart = os.path.split(fname)
    ConverterClass = converter_for_filename(filepart)
    converter = ConverterClass()
    converter.process_file(fname)
            
if __name__ == '__main__':
    for fname in sys.argv[1:]:
        convert_file(fname)
