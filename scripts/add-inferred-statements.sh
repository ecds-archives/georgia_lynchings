#!/bin/bash
scriptdir=$(dirname $0)
queryurl=${1:-http://localhost:8080/openrdf-sesame/repositories/galyn/statements}
function get_sparql () {
  awk '/^#/{next}{print}' <"$scriptdir"/add-inferred-statements.rq
}
function execute_query () {
  curl -v --data-urlencode update@- "$queryurl"
}
get_sparql | execute_query
