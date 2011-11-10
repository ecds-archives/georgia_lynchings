#!/bin/bash

# Add inferrable statements to a Sesame repository after uploading basic
# statements from the source database.
#
# USAGE: add-inferred-statements.sh [query_url]
# EXAMPLE: add-inferred-statements.sh http://host:port/openrdf-sesame/repositories/my_repo/statements
#
# The PC-ACE relational database contains lots of interesting data, but in a
# few places the relational model drives it to express relationships as rows
# in many-to-many join tables or even across multiple tables, where RDF can
# express them directly as RDF statements. The csv2rdf.py script translates
# individual row data into basic RDF statements but can't easily supplement
# this by translating these cross-table relationships directly into RDF. So
# instead, after uploading the basic RDF statements from csv2rdf.py into a
# Sesame repository, use this script to create these more complex
# statements. This script reads the SPARQL Update statements from
# add-inferred-statements.rq and sends them to the repository at the
# specified query URL to create those statements.

scriptdir=$(dirname $0)
queryurl=${1:-http://localhost:8080/openrdf-sesame/repositories/galyn/statements}
function get_sparql () {
  awk '/^#/{next}{print}' <"$scriptdir"/add-inferred-statements.rq
}
function execute_query () {
  curl -v --data-urlencode update@- "$queryurl"
}
get_sparql | execute_query
