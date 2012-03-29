#!/bin/bash

# Upload turtle (.ttl) RDF files to a Sesame repository. See usage below:

function usage () {
  cat <<EOF
usage: $0 [-r web root] [-c graph context root] file.ttl ...

Post Turtle (.ttl) RDF files into a Sesame or compatible triplestore. Derive
the graph context URI from the filename.

  -r web root: The URI that receives POSTed statements. e.g.:
        http://host:port/openrdf-sesame/repositories/myrepo/statements

  -c graph context root: You probaby don't want to customize this. It's the
        URI root to use for uploaded files. Namespaces for this project are
        rooted in files representing the tables in the source database. Use
        this argument to specify the base URL representing a directory path
        in which these table resources reside. Note that if this ever
        changes to anything other than the default context root, the path
        will need to change in several places across this project for the
        code to all work correctly together.

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
