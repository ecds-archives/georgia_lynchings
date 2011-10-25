#!/bin/bash
scriptdir=$(dirname $0)
function get_sparql () {
  awk '/^#/{next}{print}' <$scriptdir/add-inferred-statements.rq
}
function execute_query () {
  curl -v --data-urlencode update@- \
    http://localhost:8080/openrdf-sesame/repositories/galyn/statements
}
get_sparql | execute_query
