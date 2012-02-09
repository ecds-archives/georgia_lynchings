'''
This file contains a dictionary of predefined SPARQL queries, 
available for the run_sparql_query command.
'''

test_sparql_query={}
test_sparql_query['get_types']='SELECT DISTINCT ?type WHERE { ?thing a ?type . } ORDER BY ?type'  
test_sparql_query['find_subtypes']="""
PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
PREFIX sxsxcx:<http://galyn.example.com/source_data_files/setup_xref_Simplex-Complex.csv#>
PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#> 
select * where {
  {
    ?sxcxcx sxcxcx:HigherComplex scxn:Macro_Event;
            sxcxcx:Name ?name;
            sxcxcx:LowerComplex ?lower.
    ?lower scx:GrammarRule_Text ?rule.
  } UNION {
    ?sxsxcx sxsxcx:Complex scxn:Macro_Event;
            sxsxcx:Simplex ?ssx.
    ?ssx ssx:Name ?name.
  }
}
"""

# This query works in the GUI, but not in the API
test_sparql_query['find_events_order_time']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
PREFIX ssxn:<http://galyn.example.com/source_data_files/setup_Simplex.csv#name->
PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->
SELECT ?macro ?melabel ?event ?evlabel (MIN(?evdate) as ?mindate)
WHERE {
  ?macro a scxn:Macro_Event;                  
         dcx:Identifier ?melabel;
         sxcxcxn:Event ?event.         
  ?event dcx:Identifier ?evlabel;
         sxcxcxn:Semantic_Triplet ?_1.            
  ?_1 sxcxcxn:Process ?_2.               
  {
    ?_2 sxcxcxn:Simple_process ?_3. 
    ?_3 sxcxcxn:Circumstances ?_4. 
    ?_4 sxcxcxn:Time ?_5. 
  } UNION {
    ?_2 sxcxcxn:Complex_process ?_6.    
    ?_6 sxcxcxn:Simple_process ?_7. 
    ?_7 sxcxcxn:Circumstances ?_8. 
    ?_8 sxcxcxn:Time ?_5. 
  } UNION {
    ?_2 sxcxcxn:Complex_process ?_6.    
    ?_6 sxcxcxn:Other_process ?_9. 
    ?_9 sxcxcxn:Simple_process ?_7.    
    ?_7 sxcxcxn:Circumstances ?_8. 
    ?_8 sxcxcxn:Time ?_5. 
  } UNION {
    ?_2 sxcxcxn:Complex_process ?_6.    
    ?_6 sxcxcxn:Other_process ?_9. 
    ?_9 sxcxcxn:Nominalization ?_10. 
    ?_10 sxcxcxn:Time ?_5. 
  }

  ?_5 sxcxcxn:Date ?_11.  

  {
    ?_11 sxcxcxn:Definite_date ?_12.     
    ?_12 ssxn:Definite_date ?evdate      
  } UNION {
    ?_11 sxcxcxn:Indefinite_date ?_13.     
    ?_13 sxcxcxn:Reference_yardstick ?_14.      
    ?_14 ssxn:Definite_date ?evdate      
  } UNION {
    ?_11 sxcxcxn:Indefinite_date ?_13.     
    ?_13 sxcxcxn:Reference_yardstick ?_14.      
    ?_14 ssxn:Newspaper_date ?evdate 
  }
}
GROUP BY ?macro ?melabel ?event ?evlabel
ORDER BY ?mindate
"""
test_sparql_query['find_event_order_location']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
PREFIX ssxn:<http://galyn.example.com/source_data_files/setup_Simplex.csv#name->
PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->
SELECT DISTINCT ?state ?county ?city ?event ?evlabel ?macro ?melabel
WHERE {
  ?macro a scxn:Macro_Event;      
         dcx:Identifier ?melabel;
         sxcxcxn:Event ?event. 
  ?event dcx:Identifier ?evlabel;
         sxcxcxn:Semantic_Triplet ?_1.   
  ?_1 sxcxcxn:Process ?_2.    

  {
    ?_2 sxcxcxn:Simple_process ?_3.  
    ?_3 sxcxcxn:Circumstances ?_4.  
    ?_4 sxcxcxn:Space ?_5. 
  } UNION {
    ?_2 sxcxcxn:Complex_process ?_6. 
    ?_6 sxcxcxn:Simple_process ?_3. 
    ?_3 sxcxcxn:Circumstances ?_4. 
    ?_4 sxcxcxn:Space ?_5. 
  } UNION {
    ?_2 sxcxcxn:Complex_process ?_6.      
    ?_6 sxcxcxn:Other_process ?_7.     
    ?_7 sxcxcxn:Simple_process ?_3.      
    ?_3 sxcxcxn:Circumstances ?_4.    
    ?_4 sxcxcxn:Space ?_5.     
  } UNION {
    ?_2 sxcxcxn:Complex_process ?_6.      
    ?_6 sxcxcxn:Other_process ?_7.     
    ?_7 sxcxcxn:Nominalization ?_8.      
    ?_8 sxcxcxn:Space ?_5.      
  }
  {
    ?_5 sxcxcxn:Territory ?_9.               
    ?_9 sxcxcxn:Type_of_territory ?_10.              
  } UNION {
    ?_5 sxcxcxn:City ?_10.               
  }
  
  OPTIONAL {
    ?_10 ssxn:County ?county.             
    FILTER (?county != "?")
  }
  OPTIONAL {
    ?_10 ssxn:State ?state.              
    FILTER (?state != "?")
  }
  OPTIONAL {
    ?_10 ssxn:City_name ?city.              
    FILTER (?city != "?")
  }
  
  FILTER (BOUND(?state) || BOUND(?county) || BOUND(?city))
}
ORDER BY UCASE(?state) UCASE(?county) UCASE(?city) ?event ?evlabel 
"""
test_sparql_query['find_articles_for_event']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX dxcxd:<http://galyn.example.com/source_data_files/data_xref_Complex-Document.csv#>
PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
PREFIX ssxn:<http://galyn.example.com/source_data_files/setup_Simplex.csv#name->
PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->
SELECT ?macro ?melabel ?event ?evlabel ?dd ?docpath 
WHERE {
  ?macro a scxn:Macro_Event;                  
         dcx:Identifier ?melabel;
         sxcxcxn:Event ?event.         
  ?event dcx:Identifier ?evlabel.
  ?dxcxd dxcxd:Complex ?event;
         dxcxd:Document ?dd.
  ?dd ssxn:documentPath ?docpath.   
} 
ORDER BY ?macro ?event ?docpath
"""
test_sparql_query['find_events_for_specific_person']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->
SELECT ?triplet ?role ?trlabel ?event ?evlabel ?macro ?melabel 
WHERE {
  dcx:r4569 ^sxcxcxn:Individual ?actor. 
  ?actor ^sxcxcxn:Actor ?participant. 
  {
    ?triplet sxcxcxn:Participant_S ?participant. 
    BIND("subject" as ?role)
  } UNION {
    ?triplet sxcxcxn:Participant_O ?participant.  
    BIND("object" as ?role)
  } 

  ?triplet dcx:Identifier ?trlabel.
  ?event sxcxcxn:Semantic_Triplet ?triplet;       
         dcx:Identifier ?evlabel.
  ?macro sxcxcxn:Event ?event;          
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
PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
PREFIX sd:<http://galyn.example.com/source_data_files/setup_Document.csv#>
PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
PREFIX ssxn:<http://galyn.example.com/source_data_files/setup_Simplex.csv#name->
PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->
PREFIX sxsxcx:<http://galyn.example.com/source_data_files/setup_xref_Simplex-Complex.csv#>
PREFIX sxsxd:<http://galyn.example.com/source_data_files/setup_xref_Simplex-Document.csv#>
PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
'''
