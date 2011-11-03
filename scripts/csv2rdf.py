#!/usr/bin/env python

import csv
import datetime
import os
import sys
import urllib

URI_BASE = 'http://galyn.example.com/source_data_files/'

def url_from_path(fpath, base=None):
    if base is None:
        base = URI_BASE
    dirname, fname = os.path.split(fpath)
    return base + fname

class Converter(object):
    def process_file(self, in_fname):
        self.in_uri = url_from_path(in_fname)
        out_fname = self.make_output_filename(in_fname)
        with open(in_fname) as inf, open(out_fname, 'w') as outf:
            reader = csv.reader(inf)
            row_iter = iter(reader)
            columns = row_iter.next()
            
            print >>outf, '@base <%s> .' % (self.in_uri,)
            self.output_prefixes(outf)

            for row in row_iter:
                # row[0] is always ID
                print >>outf, '<#r%s> a <#Row>' % (row[0],),
                for prop, val in zip(columns, row):
                    encode = getattr(self, 'encode_' + prop, self.encode)
                    encoded = encode(val)
                    if encoded is not None:
                        print >>outf, ';\n   <#%s> %s' % (prop, encoded),
                print >>outf, '.'

    def make_output_filename(self, in_fname):
        in_base, ext = os.path.splitext(in_fname)
        out_ext = '.ttl'
        out_fname = in_base + out_ext
        i = 0
        while os.path.exists(out_fname):
            i += 1
            out_fname = '%s.%d%s' % (in_base, i, out_ext)
        return out_fname

    def output_prefixes(self, outf):
        pass
    
    def encode(self, val):
        # lacking other info, assume string
        return self._encode_as_string(val)

    def _encode_as_string(self, val):
        val = val.replace('\\', '\\\\') \
                 .replace('"', '\"')
        if '\n' in val:
            return '"""%s"""' % (val,)
        else:
            return '"%s"' % (val,)

    def _encode_as_decimal(self, val):
        if val:
            return '"%s"^^xsd:decimal' % (val,)

    def _encode_as_integer(self, val):
        if val:
            return '"%s"^^xsd:integer' % (val,)

    def _encode_as_boolean(self, val):
        if val:
            xsdval = 'false' if val == '0' else 'true'
            return '"%s"^^xsd:boolean' % (xsdval,)


class Converter_data_Complex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix scx: <setup_Complex.csv#> .'

    def encode_ComplexType(self, val):
        return 'scx:r' + val


class Converter_data_Document(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_Document, self).output_prefixes(outf)
        print >>outf, '@prefix sd: <setup_Document.csv#> .'

    def encode_DocumentType(self, val):
        return 'sd:r' + val


class Converter_data_Simplex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_Simplex, self).output_prefixes(outf)
        print >>outf, '@prefix ssx: <setup_Simplex.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_SimplexType(self, val):
        return 'ssx:r' + val

    # TODO: refValue is an index into data_Simplex*. table depends on
    # simplexType.ValueType. 1==Text; 2==Number; 3==Date. 4 indicates that
    # refValue directly encodes boolean data.

    def encode_Locked(self, val):
        return self._encode_as_boolean(val)


class Converter_data_SimplexDate(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_SimplexDate, self).output_prefixes(outf)
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_Value(self, val):
        dtval = datetime.datetime.strptime(val, '%m/%d/%y %H:%M:%S')
        dtval = dtval.replace(year=dtval.year - 100)
        return '"%s"^^xsd:dateTime' % (dtval.isoformat(),)
        

class Converter_data_SimplexNumber(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_SimplexNumber, self).output_prefixes(outf)
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_Value(self, val):
        return self._encode_as_decimal(val)


class Converter_data_SimplexText(Converter):
    pass # nothing to do?


class Converter_data_VCommentArchive(Converter):
    pass

    # TODO: What are UserID/VerifierID?

    # TODO: Do we need to split up Position macro events?


class Converter_data_xref_AnyComplex_Complex(Converter):
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
    def output_prefixes(self, outf):
        super(Converter_data_xref_comment_complex, self).output_prefixes(outf)
        print >>outf, '@prefix dcx: <data_Complex.csv#> .'

    def encode_Complex(self, val):
        return 'dcx:r' + val


class Converter_data_xref_Comment_Document(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Comment_Document, self).output_prefixes(outf)
        print >>outf, '@prefix dd: <data_Document.csv#> .'

    def encode_Document(self, val):
        return 'dd:r' + val


class Converter_data_xref_Comment_Simplex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Comment_Simplex, self).output_prefixes(outf)
        print >>outf, '@prefix dsx: <data_Simplex.csv#> .'

    def encode_Simplex(self, val):
        return 'dsx:r' + val


class Converter_data_xref_Complex_Complex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Complex_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix dcx: <data_Complex.csv#> .'
        print >>outf, '@prefix sxcxcx: <setup_xref_Complex-Complex.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_HigherComplex(self, val):
        if val != '-1':
            return 'dcx:r' + val # TODO: verify this relationship

    def encode_LowerComplex(self, val):
        if val != '-1':
            return 'dcx:r' + val # TODO: verify this relationship

    def encode_xrefID(self, val):
        return 'sxcxcx:r' + val

    def encode_Order(self, val):
        return self._encode_as_integer(val)


class Converter_data_xref_Complex_Document(Converter):
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
    def output_prefixes(self, outf):
        super(Converter_data_xref_Simplex_Document, self).output_prefixes(outf)
        print >>outf, '@prefix dxsxcx: <data_xref_Simplex-Complex.csv#> .'
        print >>outf, '@prefix dd: <data_Document.csv#> .'

    def encode_Simplex(self, val):
        return 'dxsxcx:r' + val

    def encode_Document(self, val):
        return 'dd:r' + val

class Converter_data_xref_Simplex_Simplex_Document(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Simplex_Simplex_Document, self).output_prefixes(outf)
        print >>outf, '@prefix dsx: <data_Simplex.csv#> .'
        print >>outf, '@prefix dd: <data_Document.csv#> .'
        print >>outf, '@prefix sxsxd: <setup_xref_Simplex-Document.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'
    
    def encode_xrefID(self, val):
        return 'sxsxd:r' + val

    def encode_Simplex(self, val):
        return 'dsx:r' + val

    def encode_Document(self, val):
        return 'dd:r' + val

    def encode_Order(self, val):
        return self._encode_as_integer(val)


class Converter_data_xref_VComment(Converter):
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
    # TODO: copySetting: Is this a boolean? number?
    # TODO: DocumentType: Does this reference setup_Document? maybe?
    pass


class Converter_setup_Document(Converter):
    # DocumentType looks like just a string. Leave it for now.
    pass


class Converter_setup_Simplex(Converter):
    def output_prefixes(self, outf):
        super(Converter_setup_Simplex, self).output_prefixes(outf)
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_ValueType(self, val):
        # FIXME: Represent the actual meaning of this number. Simplex data
        # with these types are:
        #   1. text (in data_SimplexText)
        #   2. number (in data_SimplexNumber)
        #   3. date (in data_SimplexDate)
        #   4. boolean, directly encoded
        #   5. time (in data_SimplexDate)
        return self._encode_as_integer(val)

    def encode_Locked(self, val):
        return self._encode_as_boolean(val)


class Converter_setup_xref_Complex_Complex(Converter):
    def output_prefixes(self, outf):
        super(Converter_setup_xref_Complex_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix scx: <setup_Complex.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

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
    basename, ext = os.path.splitext(fname)
    converter_name = 'Converter_' + basename.replace('-', '_')
    return globals().get(converter_name, Converter)

def convert_file(fname):
    dirpart, filepart = os.path.split(fname)
    ConverterClass = converter_for_filename(filepart)
    converter = ConverterClass()
    converter.process_file(fname)
            
if __name__ == '__main__':
    for fname in sys.argv[1:]:
        convert_file(fname)
