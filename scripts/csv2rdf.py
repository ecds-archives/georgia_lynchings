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

            for i, row in enumerate(row_iter):
                # i+1 here so that the id matches the line number
                print >>outf, '<#r%d> a src:Row' % (i+1,),
                for prop, val in zip(columns, row):
                    encode = getattr(self, 'encode_' + prop, self.encode)
                    encoded = encode(val)
                    if encoded is not None:
                        print >>outf, ';\n   src:%s %s' % (prop, encoded),
                print >>outf, '.'

    def make_output_filename(self, in_fname):
        in_base, ext = os.path.splitext(in_fname)
        out_fname = '%s.ttl' % (in_base,)
        i = 0
        while os.path.exists(out_fname):
            i += 1
            out_fname = '%s.%d.n3' % (in_base, i)
        return out_fname

    def output_prefixes(self, outf):
        print >>outf, '@prefix src: <%s#> .' % (self.in_uri,)
    
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

    def _encode_as_boolean(self, val):
        xsdval = 'false' if val == '0' else 'true'
        return '"%s"^^xsd:boolean' % (xsdval,)


class Converter_data_Complex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix ctype: <data/setup_Complex.csv#> .'

    def encode_ComplexType(self, val):
        return 'ctype:r' + val


class Converter_data_Document(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_Document, self).output_prefixes(outf)
        print >>outf, '@prefix dtype: <data/setup_Document.csv#> .'

    def encode_DocumentType(self, val):
        return 'dtype:r' + val


class Converter_data_Simplex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_Simplex, self).output_prefixes(outf)
        print >>outf, '@prefix stype: <data/setup_Simplex.csv#> .'
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
        return '"%s"^^xsd:integer' % (val,)


class Converter_data_SimplexText(Converter):
    pass # nothing to do?


class Converter_data_VCommentArchive(Converter):
    pass

    # TODO: What are UserID/VerifierID?

    # TODO: Do we need to split up Position macro events?


class Converter_data_xref_AnyComplex_Complex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_AnyComplex_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix cx: <data/data_Complex.csv#> .'

    def encode_Complex(self, val):
        return 'cx:r' + val
        
    # TODO: What is AnyComplex?
    def encode_AnyComplex(self, val):
        if val:
            return self._encode_as_string(val)


class Converter_data_xref_Comment_Complex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Comment_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix cx: <data/data_Complex.csv#> .'

    def encode_Complex(self, val):
        return 'cx:r' + val


class Converter_data_xref_Comment_Document(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Comment_Document, self).output_prefixes(outf)
        print >>outf, '@prefix doc: <data/data_Document.csv#> .'

    def encode_Document(self, val):
        return 'doc:r' + val


class Converter_data_xref_Comment_Simplex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Comment_Simplex, self).output_prefixes(outf)
        print >>outf, '@prefix sx: <data/data_Simplex.csv#> .'

    def encode_Simplex(self, val):
        return 'sx:r' + val


class Converter_data_xref_Complex_Complex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Complex_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix cx: <data/data_Complex.csv#> .'
        print >>outf, '@prefix xref: <data/setup_xref_Complex_Complex.csv#> .'

    def encode_HigherComplex(self, val):
        if val != '-1':
            return 'cx:r' + val # TODO: verify this relationship

    def encode_LowerComplex(self, val):
        if val != '-1':
            return 'cx:r' + val # TODO: verify this relationship

    def encode_xrefID(self, val):
        return 'xref:r' + val

    def encode_Order(self, val):
        return '"%s"^^xsd:integer' % (val,)


class Converter_data_xref_Complex_Document(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Complex_Document, self).output_prefixes(outf)
        print >>outf, '@prefix cx: <data/data_Complex.csv#> .'
        print >>outf, '@prefix doc: <data/data_Document.csv#> .'

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
        print >>outf, '@prefix cx: <data/data_Complex.csv#> .'
        print >>outf, '@prefix sx: <data/data_Simplex.csv#> .'
        print >>outf, '@prefix xref: <data/setup_xref_Simplex_Complex.csv#> .'

    def encode_xrefID(self, val):
        return 'xref:r' + val

    def encode_Simplex(self, val):
        return 'sx:r' + val

    def encode_Complex(self, val):
        return 'cx:r' + val

    def encode_Order(self, val):
        return '"%s"^^xsd:integer' % (val,)


class Converter_data_xref_Simplex_Document(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Simplex_Document, self).output_prefixes(outf)
        print >>outf, '@prefix sx: <data/data_xref_Simplex_Complex.csv#> .'
        print >>outf, '@prefix doc: <data/data_Documnet.csv#> .'

    def encode_Simplex(self, val):
        return 'sx:r' + val

    def encode_Document(self, val):
        return 'doc:r' + val

class Converter_data_xref_Simplex_Simplex_Document(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_xref_Simplex_Simplex_Document, self).output_prefixes(outf)
        print >>outf, '@prefix sx: <data/data_Simplex.csv#> .'
        print >>outf, '@prefix doc: <data/data_Documnet.csv#> .'
        print >>outf, '@prefix xref: <data/setup_xref_Simplex_Document.csv#> .'
    
    def encode_xrefID(self, val):
        return 'xref:r' + val

    def encode_Simplex(self, val):
        return 'sx:r' + val

    def encode_Document(self, val):
        return 'doc:r' + val

    def encode_Order(self, val):
        return '"%s"^^xsd:integer' % (val,)


class Converter_data_xref_VComment(Converter):
    # TODO: this table is undocumented. many fields guessed or entirely unknown

    def output_prefixes(self, outf):
        super(Converter_data_xref_VComment, self).output_prefixes(outf)
        print >>outf, '@prefix cx: <data/data_Complex.csv#> .'

    def encode_Complex(self, val):
        return 'cx:r' + val

    def encode_Completed(self, val):
        return self._encode_as_boolean(val)


class Converter_data_xref_VComment_Document(Converter):
    # TODO: this table is undocumented. many fields guessed or entirely unknown

    def output_prefixes(self, outf):
        super(Converter_data_xref_VComment_Document, self).output_prefixes(outf)
        print >>outf, '@prefix cx: <data/data_Complex.csv#> .'

    def encode_Complex(self, val):
        return 'cx:r' + val

    def encode_Completed(self, val):
        return self._encode_as_boolean(val)


CONVERTERS = {
    'data_Complex': Converter_data_Complex,
    'data_Document': Converter_data_Document,
    'data_Simplex': Converter_data_Simplex,
    'data_SimplexDate': Converter_data_SimplexDate,
    'data_SimplexNumber': Converter_data_SimplexNumber,
    'data_SimplexText': Converter_data_SimplexText,
    'data_VCommentArchive': Converter_data_VCommentArchive,
    'data_xref_AnyComplex_Complex': Converter_data_xref_AnyComplex_Complex,
    'data_xref_Comment_Complex': Converter_data_xref_Comment_Complex,
    'data_xref_Comment_Document': Converter_data_xref_Comment_Document,
    'data_xref_Comment_Simplex': Converter_data_xref_Comment_Simplex,
    'data_xref_Complex_Complex': Converter_data_xref_Complex_Complex,
    'data_xref_Complex_Document': Converter_data_xref_Complex_Document,
    'data_xref_Simplex_Complex': Converter_data_xref_Simplex_Complex,
    'data_xref_Simplex_Document': Converter_data_xref_Simplex_Document,
    'data_xref_Simplex_Simplex_Document': Converter_data_xref_Simplex_Simplex_Document,
    'data_xref_VComment': Converter_data_xref_VComment,
    'data_xref_VComment_Document': Converter_data_xref_VComment_Document,
}
def convert_file(fname):
    dirpart, filepart = os.path.split(fname)
    basename, ext = os.path.splitext(filepart)
    ConverterClass = CONVERTERS.get(basename, Converter)
    converter = ConverterClass()
    converter.process_file(fname)
            
if __name__ == '__main__':
    for fname in sys.argv[1:]:
        convert_file(fname)
