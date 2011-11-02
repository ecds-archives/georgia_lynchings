#!/bin/bash

function usage () {
  cat <<EOF
usage: $0 [-c graph context root] [-r web root] file.ttl ...

Post Turtle (.ttl) files into a Sesame or compatible triplestore. Derive the
graph context URI from the filename (use -c to alter the base for this URI).
EOF
}

WEB_ROOT=http://localhost:8080/openrdf-sesame/repositories/galyn/statements
CONTEXT_ROOT=http://galyn.example.com/source_data_files/

while getopts "c:hr:" opt; do
  case $opt in
    h) usage; exit 1;;
    c) CONTEXT_ROOT=$OPTARG;;
    r) WEB_ROOT=$OPTARG;;
    ?) usage; exit 1;;
  esac
done
shift $((OPTIND-1))

while [ $# -gt 0 ]; do 
  fname=$1
  base=$(basename $fname)
  shift

  curl -v -T $fname -H 'Content-Type: text/turtle' \
       "$WEB_ROOT?context=%3C$CONTEXT_ROOT$base%3e";
done
