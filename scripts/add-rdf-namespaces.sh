#!/bin/bash

function usage () {
  cat <<EOF
usage: $0 [-b file base URI] [-r Sesame repository]

Initialize a Sesame repository with common namespaces used in this project.
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
dxacxcx	data_xref_AnyComplex_Complex.csv
dxctcx	data_xref_Comment_Complex.csv
dxctd	data_xref_Comment_Document.csv
dxctsx	data_xref_Comment_Simplex.csv
dxcxcx	data_xref_Complex_Complex.csv
dxcxd	data_xref_Complex_Document.csv
dxsxcx	data_xref_Simplex_Complex.csv
dxsxd	data_xref_Simplex_Document.csv
dxsxsxd	data_xref_Simplex_Simplex_Document.csv
dxvctd	data_xref_VComment_Document.csv
dxvct	data_xref_VComment.csv
scx	setup_Complex.csv
sd	setup_Document.csv
ssx	setup_Simplex.csv
sxcxcx	setup_xref_Complex_Complex.csv
sxsxcx	setup_xref_Simplex_Complex.csv
sxsxd	setup_xref_Simplex_Document.csv
EOF
