#!/usr/bin/env python

import csv
import datetime
import os
import sys
import urllib

class Converter(object):
    def process_file(self, in_fname):
        self.in_uri = urllib.pathname2url(in_fname)
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

    def _encode_as_integer(self, val):
        return '"%s"^^xsd:integer' % (val,)

    def _encode_as_boolean(self, val):
        xsdval = 'false' if val == '0' else 'true'
        return '"%s"^^xsd:boolean' % (xsdval,)


class Converter_data_Complex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix ctype: <setup_Complex.csv#> .'

    def encode_ComplexType(self, val):
        return 'ctype:r' + val


class Converter_data_Document(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_Document, self).output_prefixes(outf)
        print >>outf, '@prefix dtype: <setup_Document.csv#> .'

    def encode_DocumentType(self, val):
        return 'dtype:r' + val


class Converter_data_Simplex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_Simplex, self).output_prefixes(outf)
        print >>outf, '@prefix stype: <setup_Simplex.csv#> .'
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_SimplexType(self, val):
        return 'stype:r' + val

    # TODO: refValue is an index into data_Simplex*. table depends on
    # simplexType.ValueType. 1==Text; 2==Number; 3==Date. 4 indicates that
    # refValue directly encodes boolean data.

    def encode_Locked(self, val):
        return self._encode_as_boolean(val)


class Converter_data_SimplexDate(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_SimplexDate, self).output_prefixes(outf)
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#>'

    def encode_Value(self, val):
        dtval = datetime.datetime.strptime(val, '%m/%d/%y %H:%M:%S')
        dtval = dtval.replace(year=dtval.year - 100)
        return '"%s"^^xsd:dateTime' % (dtval.isoformat(),)
        

class Converter_data_SimplexNumber(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_SimplexNumber, self).output_prefixes(outf)
        print >>outf, '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .'

    def encode_Value(self, val):
        return self._encode_as_integer(val)


class Converter_data_SimplexText(Converter):
    pass # nothing to do?


class Converter_data_VCommentArchive(Converter):
    pass

    # TODO: What are UserID/VerifierID?

    # TODO: Do we need to split up Position macro events?


class Converter_data_xref_AnyComplex_Complex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_AnyComplex_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix cx: <data_Complex.csv#> .'

    def encode_Complex(self, val):
        return 'cx:r' + val
        
    # TODO: What is AnyComplex?
    def encode_AnyComplex(self, val):
        if val:
            return self._encode_as_string(val)


class Converter_data_xref_Comment_Complex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Comment_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix cx: <data_Complex.csv#> .'

    def encode_Complex(self, val):
        return 'cx:r' + val


class Converter_data_xref_Comment_Document(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Comment_Document, self).output_prefixes(outf)
        print >>outf, '@prefix doc: <data_Document.csv#> .'

    def encode_Document(self, val):
        return 'doc:r' + val


class Converter_data_xref_Comment_Simplex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Comment_Simplex, self).output_prefixes(outf)
        print >>outf, '@prefix sx: <data_Simplex.csv#> .'

    def encode_Simplex(self, val):
        return 'sx:r' + val


class Converter_data_xref_Complex_Complex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Complex_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix cx: <data_Complex.csv#> .'
        print >>outf, '@prefix xref: <setup_xref_Complex_Complex.csv#> .'

    def encode_HigherComplex(self, val):
        if val != '-1':
            return 'cx:r' + val # TODO: verify this relationship

    def encode_LowerComplex(self, val):
        if val != '-1':
            return 'cx:r' + val # TODO: verify this relationship

    def encode_xrefID(self, val):
        return 'xref:r' + val

    def encode_Order(self, val):
        return self._encode_as_integer(val)


class Converter_data_xref_Complex_Document(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Complex_Document, self).output_prefixes(outf)
        print >>outf, '@prefix cx: <data_Complex.csv#> .'
        print >>outf, '@prefix doc: <data_Document.csv#> .'

    def encode_Complex(self, val):
        return 'cx:r' + val

    def encode_Document(self, val):
        return 'doc:r' + val

    def encode_Complete(self, val):
        return self._encode_as_boolean(val)

    def encode_Verified(self, val):
        return self._encode_as_boolean(val)


class Converter_data_xref_Simplex_Complex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Simplex_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix cx: <data_Complex.csv#> .'
        print >>outf, '@prefix sx: <data_Simplex.csv#> .'
        print >>outf, '@prefix xref: <setup_xref_Simplex_Complex.csv#> .'

    def encode_xrefID(self, val):
        return 'xref:r' + val

    def encode_Simplex(self, val):
        return 'sx:r' + val

    def encode_Complex(self, val):
        return 'cx:r' + val

    def encode_Order(self, val):
        return self._encode_as_integer(val)


class Converter_data_xref_Simplex_Document(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Simplex_Document, self).output_prefixes(outf)
        print >>outf, '@prefix sx: <data_xref_Simplex_Complex.csv#> .'
        print >>outf, '@prefix doc: <data_Documnet.csv#> .'

    def encode_Simplex(self, val):
        return 'sx:r' + val

    def encode_Document(self, val):
        return 'doc:r' + val

class Converter_data_xref_Simplex_Simplex_Document(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Simplex_Simplex_Document, self).output_prefixes(outf)
        print >>outf, '@prefix sx: <data_Simplex.csv#> .'
        print >>outf, '@prefix doc: <data_Documnet.csv#> .'
        print >>outf, '@prefix xref: <setup_xref_Simplex_Document.csv#> .'
    
    def encode_xrefID(self, val):
        return 'xref:r' + val

    def encode_Simplex(self, val):
        return 'sx:r' + val

    def encode_Document(self, val):
        return 'doc:r' + val

    def encode_Order(self, val):
        return self._encode_as_integer(val)


class Converter_data_xref_VComment(Converter):
    # TODO: this table is undocumented. many fields guessed or entirely unknown

    def output_prefixes(self, outf):
        super(Converter_data_xref_VComment, self).output_prefixes(outf)
        print >>outf, '@prefix cx: <data_Complex.csv#> .'

    def encode_Complex(self, val):
        return 'cx:r' + val

    def encode_Completed(self, val):
        return self._encode_as_boolean(val)


class Converter_data_xref_VComment_Document(Converter):
    # TODO: this table is undocumented. many fields guessed or entirely unknown

    def output_prefixes(self, outf):
        super(Converter_data_xref_VComment_Document, self).output_prefixes(outf)
        print >>outf, '@prefix cx: <data_Complex.csv#> .'

    def encode_Complex(self, val):
        return 'cx:r' + val

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
        print >>outf, '@prefix cx: <setup_Complex.csv#> .'

    def encode_HigherComplex(self, val):
        if val != '-1':
            return 'cx:r' + val
        
    def encode_LowerComplex(self, val):
        if val != '-1':
            return 'cx:r' + val
        
    # TODO: What is Relationship?

    def encode_Order(self, val):
        return self._encode_as_integer(val)

    # TODO: What is Group?

    def encode_Required(self, val):
        return self._encode_as_boolean(val)

    def encode_AllowMultiple(self, val):
        return self._encode_as_boolean(val)
        
    # TODO: What is Autoxref?


def convert_file(fname):
    dirpart, filepart = os.path.split(fname)
    basename, ext = os.path.splitext(filepart)
    converter_name = 'Converter_' + basename
    ConverterClass = globals().get(converter_name, Converter)
    converter = ConverterClass()
    converter.process_file(fname)
            
if __name__ == '__main__':
    for fname in sys.argv[1:]:
        convert_file(fname)
