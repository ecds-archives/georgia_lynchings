#!/bin/bash

# Add common RDF namespaces for this project to a Sesame repository. See
# usage below:

function usage () {
  cat <<EOF
usage: $0 [-b file base URI] [-r Sesame repository]

Initialize a Sesame repository with common namespaces used in this project.

  -r Sesame repository: The URI of the repository to receive the namespace
        definitions. e.g., http://host:port/openrdf-sesame/repositories/myrepo

  -b file base URI: You probaby don't want to customize this. It's the URI
        root to use for uploaded files. Namespaces for this project are
        rooted in files representing the tables in the source database. Use
        this argument to specify the base URL representing a directory path
        in which these table resources reside. Note that if this ever
        changes to anything other than the default URI root, the path will
        need to change in several places across this project for the code to
        all work correctly together.

EOF
}

WEB_ROOT=http://localhost:8080/openrdf-sesame/repositories/galyn
BASE_URI=http://galyn.example.com/source_data_files/

while getopts "b:hr:" opt; do
  case $opt in
    h) usage; exit 1;;
    b) BASE_URI=$OPTARG;;
    r) WEB_ROOT=$OPTARG;;
    ?) usage; exit 1;;
  esac
done

while read ns uri; do
  echo "$BASE_URI$uri#" | curl -T - -H 'Content-Type: text/plain' \
    "$WEB_ROOT/namespaces/$ns"
done << EOF
dcx	data_Complex.csv
dd	data_Document.csv
dsxd	data_SimplexDate.csv
dsxn	data_SimplexNumber.csv
dsxt	data_SimplexText.csv
dsx	data_Simplex.csv
dttcu	data_TempTranslatorCU.csv
dvcta	data_VCommentArchive.csv
dxacxcx	data_xref_AnyComplex-Complex.csv
dxctcx	data_xref_comment-complex.csv
dxctd	data_xref_Comment-Document.csv
dxctsx	data_xref_Comment-Simplex.csv
dxcxcx	data_xref_Complex-Complex.csv
dxcxd	data_xref_Complex-Document.csv
dxsxcx	data_xref_Simplex-Complex.csv
dxsxd	data_xref_Simplex-Document.csv
dxsxsxd	data_xref_Simplex-Simplex-Document.csv
dxvctd	data_xref_VComment-Document.csv
dxvct	data_xref_VComment.csv
scx	setup_Complex.csv
sd	setup_Document.csv
ssx	setup_Simplex.csv
sxcxcx	setup_xref_Complex-Complex.csv
sxsxcx	setup_xref_Simplex-Complex.csv
sxsxd	setup_xref_Simplex-Document.csv
EOF
