#!/usr/bin/env python

import csv
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
        val = val.replace('\\', '\\\\') \
                 .replace('"', '\"')
        if '\n' in val:
            return '"""%s"""' % (val,)
        else:
            return '"%s"' % (val,)


class Converter_data_Complex(Converter):
    def output_prefixes(self, outf):
        super(Converter_data_Complex, self).output_prefixes(outf)
        print >>outf, '@prefix ctype: <data/setup_Complex#>' # FIXME: unverified

    def encode_ID(self, val):
        return None

    def encode_ComplexType(self, val):
        return 'ctype:r' + val
        

CONVERTERS = {
    'data_Complex': Converter_data_Complex,
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
