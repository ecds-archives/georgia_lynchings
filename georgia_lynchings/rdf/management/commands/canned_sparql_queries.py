'''
This file contains a dictionary of predefined SPARQL queries, 
available for the run_sparql_query command.
'''

test_sparql_query={}
test_sparql_query['get_types']='SELECT DISTINCT ?type WHERE { ?thing a ?type . } ORDER BY ?type'  
test_sparql_query['find_subtypes']="""
PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
PREFIX sxsxcx:<http://galyn.example.com/source_data_files/setup_xref_Simplex-Complex.csv#>
PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#> 
select * where {
  {
    ?sxcxcx sxcxcx:HigherComplex scx:r1;
            sxcxcx:Name ?name;
            sxcxcx:LowerComplex ?lower.
    ?lower scx:GrammarRule_Text ?rule.
  } UNION {
    ?sxsxcx sxsxcx:Complex scx:r1;
            sxsxcx:Simplex ?ssx.
    ?ssx ssx:Name ?name.
  }
}
"""

# This query works in the GUI, but not in the API
test_sparql_query['find_events_order_time']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
SELECT ?macro ?melabel ?event ?evlabel (MIN(?evdate) as ?mindate)
WHERE {
  ?macro a scx:r1;                  
         dcx:Identifier ?melabel;
         sxcxcx:r61 ?event.         
  ?event dcx:Identifier ?evlabel;
         sxcxcx:r62 ?_1.            
  ?_1 sxcxcx:r64 ?_2.               
  {
    ?_2 sxcxcx:r78 ?_3. 
    ?_3 sxcxcx:r103 ?_4. 
    ?_4 sxcxcx:r104 ?_5. 
  } UNION {
    ?_2 sxcxcx:r47 ?_6.    
    ?_6 sxcxcx:r79 ?_7. 
    ?_7 sxcxcx:r103 ?_8. 
    ?_8 sxcxcx:r104 ?_5. 
  } UNION {
    ?_2 sxcxcx:r47 ?_6.    
    ?_6 sxcxcx:r80 ?_9. 
    ?_9 sxcxcx:52 ?_7.    
    ?_7 sxcxcx:r103 ?_8. 
    ?_8 sxcxcx:r104 ?_5. 
  } UNION {
    ?_2 sxcxcx:r47 ?_6.    
    ?_6 sxcxcx:r80 ?_9. 
    ?_9 sxcxcx:r53 ?_10. 
    ?_10 sxcxcx:r60 ?_5. 
  }

  ?_5 sxcxcx:r20 ?_11.  

  {
    ?_11 sxcxcx:r97 ?_12.     
    ?_12 ssx:r66 ?evdate      
  } UNION {
    ?_11 sxcxcx:r22 ?_13.     
    ?_13 sxcxcx:r4 ?_14.      
    ?_14 ssx:r66 ?evdate      
  } UNION {
    ?_11 sxcxcx:r22 ?_13.     
    ?_13 sxcxcx:r4 ?_14.      
    ?_14 ssx:r68 ?evdate 
  }
}
GROUP BY ?macro ?melabel ?event ?evlabel
ORDER BY ?mindate
"""
test_sparql_query['find_event_order_location']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
SELECT DISTINCT ?state ?county ?city ?event ?evlabel ?macro ?melabel
WHERE {
  ?macro a scx:r1;      
         dcx:Identifier ?melabel;
         sxcxcx:r61 ?event. 
  ?event dcx:Identifier ?evlabel;
         sxcxcx:r62 ?_1.   
  ?_1 sxcxcx:r64 ?_2.    

  {
    ?_2 sxcxcx:r78 ?_3.  
    ?_3 sxcxcx:r103 ?_4.  
    ?_4 sxcxcx:r106 ?_5. 
  } UNION {
    ?_2 sxcxcx:r47 ?_6. 
    ?_6 sxcxcx:r79 ?_3. 
    ?_3 sxcxcx:r103 ?_4. 
    ?_4 sxcxcx:r106 ?_5. 
  } UNION {
    ?_2 sxcxcx:r47 ?_6.      
    ?_6 sxcxcx:r80 ?_7.     
    ?_7 sxcxcx:52 ?_3.      
    ?_3 sxcxcx:r103 ?_4.    
    ?_4 sxcxcx:r106 ?_5.     
  } UNION {
    ?_2 sxcxcx:r47 ?_6.      
    ?_6 sxcxcx:r80 ?_7.     
    ?_7 sxcxcx:r53 ?_8.      
    ?_8 sxcxcx:r59 ?_5.      
  }
  {
    ?_5 sxcxcx:r2 ?_9.               
    ?_9 sxcxcx:r41 ?_10.              
  } UNION {
    ?_5 sxcxcx:r3 ?_10.               
  }
  
  OPTIONAL {
    ?_10 ssx:r18 ?county.             
    FILTER (?county != "?")
  }
  OPTIONAL {
    ?_10 ssx:r30 ?state.              
    FILTER (?state != "?")
  }
  OPTIONAL {
    ?_10 ssx:r55 ?city.              
    FILTER (?city != "?")
  }
  
  FILTER (BOUND(?state) || BOUND(?county) || BOUND(?city))
}
ORDER BY UCASE(?state) UCASE(?county) UCASE(?city) ?event ?evlabel 
"""
test_sparql_query['find_articles_for_event']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX dxcxd:<http://galyn.example.com/source_data_files/data_xref_Complex-Document.csv#>
PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
SELECT ?macro ?melabel ?event ?evlabel ?dd ?docpath 
WHERE {
  ?macro a scx:r1;                  
         dcx:Identifier ?melabel;
         sxcxcx:r61 ?event.         
  ?event dcx:Identifier ?evlabel.
  ?dxcxd dxcxd:Complex ?event;
         dxcxd:Document ?dd.
  ?dd ssx:r85 ?docpath.   
} 
ORDER BY ?macro ?event ?docpath
"""
test_sparql_query['find_events_for_specific_person']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
SELECT ?triplet ?role ?trlabel ?event ?evlabel ?macro ?melabel 
WHERE {
  dcx:r4569 ^sxcxcx:r31 ?actor. 
  {
    ?actor ^sxcxcx:r30 ?participant. 
    ?triplet sxcxcx:r63 ?participant. 
    BIND("subject" as ?role)
  } UNION {
    ?actor ^sxcxcx:r35 ?participant.  
    ?triplet sxcxcx:r65 ?participant.  
    BIND("object" as ?role)
  } 

  ?triplet dcx:Identifier ?trlabel.
  ?event sxcxcx:r62 ?triplet;       
         dcx:Identifier ?evlabel.
  ?macro sxcxcx:r61 ?event;          
         dcx:Identifier ?melabel.      
}
"""

'''
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX dd:<http://galyn.example.com/source_data_files/data_Document.csv#>
PREFIX dsxd:<http://galyn.example.com/source_data_files/data_SimplexDate.csv#>
PREFIX dsxn:<http://galyn.example.com/source_data_files/data_SimplexNumber.csv#>
PREFIX dsxt:<http://galyn.example.com/source_data_files/data_SimplexText.csv#>
PREFIX dsx:<http://galyn.example.com/source_data_files/data_Simplex.csv#>
PREFIX dttcu:<http://galyn.example.com/source_data_files/data_TempTranslatorCU.csv#>
PREFIX dvcta:<http://galyn.example.com/source_data_files/data_VCommentArchive.csv#>
PREFIX dxacxcx:<http://galyn.example.com/source_data_files/data_xref_AnyComplex-Complex.csv#>
PREFIX dxctcx:<http://galyn.example.com/source_data_files/data_xref_comment-complex.csv#>
PREFIX dxctd:<http://galyn.example.com/source_data_files/data_xref_Comment-Document.csv#>
PREFIX dxctsx:<http://galyn.example.com/source_data_files/data_xref_Comment-Simplex.csv#>
PREFIX dxcxcx:<http://galyn.example.com/source_data_files/data_xref_Complex-Complex.csv#>
PREFIX dxcxd:<http://galyn.example.com/source_data_files/data_xref_Complex-Document.csv#>
PREFIX dxsxcx:<http://galyn.example.com/source_data_files/data_xref_Simplex-Complex.csv#>
PREFIX dxsxd:<http://galyn.example.com/source_data_files/data_xref_Simplex-Document.csv#>
PREFIX dxsxsxd:<http://galyn.example.com/source_data_files/data_xref_Simplex-Simplex-Document.csv#>
PREFIX dxvctd:<http://galyn.example.com/source_data_files/data_xref_VComment-Document.csv#>
PREFIX dxvct:<http://galyn.example.com/source_data_files/data_xref_VComment.csv#>
PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
PREFIX sd:<http://galyn.example.com/source_data_files/setup_Document.csv#>
PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
PREFIX sxsxcx:<http://galyn.example.com/source_data_files/setup_xref_Simplex-Complex.csv#>
PREFIX sxsxd:<http://galyn.example.com/source_data_files/setup_xref_Simplex-Document.csv#>
PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
'''
