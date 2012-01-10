'''
This file contains a dictionary of predefined SPARQL queries.
'''

actors={}
articles={}
events={}

actors['events']="""
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
    SELECT ?actorlabel ?triplet ?role ?trlabel ?event ?evlabel ?macro ?melabel 
    WHERE {
      ?individual ^sxcxcx:r31 ?actor;
            dcx:Identifier ?actorlabel.
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

articles['all']="""
    prefix dd: <http://galyn.example.com/source_data_files/data_Document.csv#>
    prefix ssx: <http://galyn.example.com/source_data_files/setup_Simplex.csv#>

    select ?id ?paperdate ?papername ?articlepage ?docpath where {
        ?dd a dd:Row;
            dd:ID ?id.
        optional { ?dd ssx:r68 ?paperdate }
        optional { ?dd ssx:r69 ?papername }
        optional { ?dd ssx:r73 ?articlepage }
        optional { ?dd ssx:r85 ?docpath }
    }
"""

'Find articles related to a MacroEvent'
events['articles']="""
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX dxcxd:<http://galyn.example.com/source_data_files/data_xref_Complex-Document.csv#>
    PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
    PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
    PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>

    SELECT DISTINCT ?melabel ?event ?evlabel ?dd ?docpath ?paperdate ?papername ?articlepage
    WHERE {
      # First find all of the Macro events and all of the Events for those
      # Macros. Macros aren't strictly necessary, but they're provided
      # here for
      # context.
      ?macro a scx:r1;                   # Macro event
             dcx:Identifier ?melabel;
             sxcxcx:r61 ?event.          # Event
      ?event dcx:Identifier ?evlabel.

      # Report URI and file path of each document for the event
      ?dxcxd dxcxd:Complex ?event;
             dxcxd:Document ?dd.
      optional { ?dd ssx:r68 ?paperdate }
      optional { ?dd ssx:r69 ?papername }
      optional { ?dd ssx:r73 ?articlepage }
      optional { ?dd ssx:r85 ?docpath }              
                    }
    ORDER BY ?event ?docpath
"""

'Find cities related to a MacroEvent'
events['cities']="""
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
    PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
    PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>

    SELECT DISTINCT ?city ?event ?evlabel ?melabel
    WHERE {
      # First find all the Macro events, all fo the Events for those macros,
      # and all fo the Triplets for those events. We'll be looking in these
      # triplets for locations.
      # Note: Technically we don't need the Macro events. They're provided here
      # only for context.
      ?macro a scx:r1;                    # Macro event
             dcx:Identifier ?melabel;
             sxcxcx:r61 ?event.           # Event
      ?event dcx:Identifier ?evlabel;
             sxcxcx:r62 ?_1.              # Semantic Triplet

      # Every Triplet has a Process
      ?_1 sxcxcx:r64 ?_2.                 # Process

      # We need all of the places for that Process. There are four ways
      # they might be expressed:
      {
        ?_2 sxcxcx:r78 ?_3.               # Simple process
        ?_3 sxcxcx:r103 ?_4.              # Circumstances
        ?_4 sxcxcx:r106 ?_5.              # Space
      } UNION {
        ?_2 sxcxcx:r47 ?_6.               # Complex process
        ?_6 sxcxcx:r79 ?_3.               # Simple process
        ?_3 sxcxcx:r103 ?_4.              # Circumstances
        ?_4 sxcxcx:r106 ?_5.              # Space
      } UNION {
        ?_2 sxcxcx:r47 ?_6.               # Complex process
        ?_6 sxcxcx:r80 ?_7.               # Other process
        ?_7 sxcxcx:52 ?_3.                # Simple process
        ?_3 sxcxcx:r103 ?_4.              # Circumstances
        ?_4 sxcxcx:r106 ?_5.              # Space
      } UNION {
        ?_2 sxcxcx:r47 ?_6.               # Complex process
        ?_6 sxcxcx:r80 ?_7.               # Other process
        ?_7 sxcxcx:r53 ?_8.               # Nominalization
        ?_8 sxcxcx:r59 ?_5.               # Space
      }

      # Regardless of which way we came, ?_5 is some sort of place. If
      # we're going to get from there to location simplex data, this
      # is how we get there:
      {
        ?_5 sxcxcx:r3 ?_10.               # City
      }

      # Grab the simplex data we're interested in, whichever are
      # available (but note that "?" is equivalent to missing data)
      OPTIONAL {
        ?_10 ssx:r55 ?city.               # City
        FILTER (?city != "?")
      }

      # And grab only those records that have at least one data point.
      FILTER (BOUND(?city))
    }
    # Order by UCASE to fold case.
    ORDER BY UCASE(?city) ?event ?evlabel
"""

'Find date range for a MacroEvent'
events['date_range']="""
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
    PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
    PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
    SELECT ?macro ?melabel ?event ?evlabel (MIN(?evdate) as ?mindate) (MAX(?evdate) as ?maxdate)
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

'Find locations related to a MacroEvent'
events['locations']="""
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
    PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
    PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>

    SELECT DISTINCT ?state ?county ?city ?event ?evlabel ?melabel
    WHERE {
      # First find all the Macro events, all fo the Events for those macros,
      # and all fo the Triplets for those events. We'll be looking in these
      # triplets for locations.
      # Note: Technically we don't need the Macro events. They're provided here
      # only for context.
      ?macro a scx:r1;                    # Macro event
             dcx:Identifier ?melabel;
             sxcxcx:r61 ?event.           # Event
      ?event dcx:Identifier ?evlabel;
             sxcxcx:r62 ?_1.              # Semantic Triplet

      # Every Triplet has a Process
      ?_1 sxcxcx:r64 ?_2.                 # Process

      # We need all of the places for that Process. There are four ways
      # they might be expressed:
      {
        ?_2 sxcxcx:r78 ?_3.               # Simple process
        ?_3 sxcxcx:r103 ?_4.              # Circumstances
        ?_4 sxcxcx:r106 ?_5.              # Space
      } UNION {
        ?_2 sxcxcx:r47 ?_6.               # Complex process
        ?_6 sxcxcx:r79 ?_3.               # Simple process
        ?_3 sxcxcx:r103 ?_4.              # Circumstances
        ?_4 sxcxcx:r106 ?_5.              # Space
      } UNION {
        ?_2 sxcxcx:r47 ?_6.               # Complex process
        ?_6 sxcxcx:r80 ?_7.               # Other process
        ?_7 sxcxcx:52 ?_3.                # Simple process
        ?_3 sxcxcx:r103 ?_4.              # Circumstances
        ?_4 sxcxcx:r106 ?_5.              # Space
      } UNION {
        ?_2 sxcxcx:r47 ?_6.               # Complex process
        ?_6 sxcxcx:r80 ?_7.               # Other process
        ?_7 sxcxcx:r53 ?_8.               # Nominalization
        ?_8 sxcxcx:r59 ?_5.               # Space
      }

      # Regardless of which way we came, ?_5 is some sort of place. If
      # we're going to get from there to location simplex data, there
      # are two different ways we can get there:
      {
        ?_5 sxcxcx:r2 ?_9.                # Territory
        ?_9 sxcxcx:r41 ?_10.              # Type of territory
      } UNION {
        ?_5 sxcxcx:r3 ?_10.               # City
      }

      # Grab the simplex data we're interested in, whichever are
      # available (but note that "?" is equivalent to missing data)
      OPTIONAL {
        ?_10 ssx:r18 ?county.             # County
        FILTER (?county != "?")
      }
      OPTIONAL {
        ?_10 ssx:r30 ?state.              # State
        FILTER (?state != "?")
      }
      OPTIONAL {
        ?_10 ssx:r55 ?city.               # City
        FILTER (?city != "?")
      }

      # And grab only those records that have at least one data point.
      FILTER (BOUND(?state) || BOUND(?county) || BOUND(?city))
    }
    # Order by UCASE to fold case.
    ORDER BY UCASE(?city) UCASE(?county) UCASE(?state) ?event ?evlabel
"""

'Find all Macro Events'
events['all']="""
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX dxcxd:<http://galyn.example.com/source_data_files/data_xref_Complex-Document.csv#>
    PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
    PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
    PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>

    SELECT ?macro ?melabel (COUNT(?dd) AS ?articleTotal)
    WHERE {
      ?macro a scx:r1;                   # Macro event
             dcx:Identifier ?melabel;
             sxcxcx:r61 ?event.          # Event
      ?event dcx:Identifier ?evlabel.

      # Report count of documents for macro event
      ?dxcxd dxcxd:Complex ?event;
             dxcxd:Document ?dd.    

    }
    GROUP BY ?macro ?melabel
"""

'Find detail information about Participant-O Actor'
events['parto']="""
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
    PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
    PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
    PREFIX sxsxcx:<http://galyn.example.com/source_data_files/setup_xref_Simplex-Complex.csv#>
    SELECT DISTINCT ?lname ?quantitative_age ?race ?gender ?name_of_indivd_actor ?individual ?parto ?actor ?event ?evlabel ?melabel ?macro
    WHERE {
        # First find all the Macro events, and all the Events for those macros,
        # and all of the Triplets for those events, and all the Participant-O
        # for each triplet. We'll be looking in these for detail information.
        ?macro a scx:r1; # Macro event
            dcx:Identifier ?melabel;
            sxcxcx:r61 ?event. # Event
        ?event dcx:Identifier ?evlabel;
            sxcxcx:r62 ?_1. # Semantic Triplet
        # Every Triplet has a Participant-O
        ?_1 sxcxcx:r65 ?parto. # Participant-O

        # We need all of the individuals for that Semantic Triplet.
        {
            ?parto sxcxcx:r35 ?actor. # Participant-O has an Actor
            ?actor sxcxcx:r31 ?individual. # Actor has a Individual
        }

        # Provide Name_of_individual_actor, if it exists
        OPTIONAL {
            ?individual ssx:r45 ?name_of_indivd_actor. # Name_of_individual_actor
            FILTER (?name_of_indivd_actor != "?")
        }

        # Provide Gender, if it exists
        OPTIONAL {
            ?individual sxcxcx:r34 ?pchar. # Individual has a Personal_Characteristic
            ?pchar ssx:r11 ?gender. # Gender
            FILTER (?gender != "?")
        }

        # Provide Race, if it exists
        OPTIONAL {
            ?individual sxcxcx:r34 ?pchar. # Individual has a Personal_Characteristic
            ?pchar ssx:r53 ?race. # Race
            FILTER (?race != "?")
        }

        # Provide Quantitative Age, if it exists
        OPTIONAL {
            ?individual sxcxcx:r34 ?pchar. # Individual has a Personal_Characteristic
            ?pchar sxcxcx:r89 ?age. # Personal_Characteristic has an Age
            ?age ssx:r76 ?quantitative_age. # Quantitative Age
            FILTER (?quantitative_age != "?")
        }

        # Provide Last Name, if it exists
        OPTIONAL {
            ?individual sxcxcx:r34 ?pchar. # Individual has a Personal_Characteristic
            ?pchar sxcxcx:r5 ?name. # Personal_Characteristic has an First and Last Name
            ?name ssx:r10 ?lname. # Last Name
            FILTER (?lname != "?")
        }
    }
"""


'Find detail information about Participant-S Actor'
events['parts']="""
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
    PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
    PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>
    PREFIX sxsxcx:<http://galyn.example.com/source_data_files/setup_xref_Simplex-Complex.csv#>
    SELECT DISTINCT ?lname ?quantitative_age ?race ?gender ?name_of_indivd_actor ?individual ?parts ?actor ?event ?evlabel ?melabel ?macro
    WHERE {
        # First find all the Macro events, and all the Events for those macros,
        # and all of the Triplets for those events, and all the Participant-S
        # for each triplet. We'll be looking in these for detail information.
        ?macro a scx:r1; # Macro event
            dcx:Identifier ?melabel;
            sxcxcx:r61 ?event. # Event
        ?event dcx:Identifier ?evlabel;
            sxcxcx:r62 ?_1. # Semantic Triplet
        # Every Triplet has a Participant-S
        ?_1 sxcxcx:r63 ?parto. # Participant-S

        # We need all of the individuals for that Semantic Triplet.
        {
            ?parto sxcxcx:r30 ?actor. # Participant-S has an Actor
            ?actor sxcxcx:r31 ?individual. # Actor has a Individual
        }

        # Provide Name_of_individual_actor, if it exists
        OPTIONAL {
            ?individual ssx:r45 ?name_of_indivd_actor. # Name_of_individual_actor
            FILTER (?name_of_indivd_actor != "?")
        }

        # Provide Gender, if it exists
        OPTIONAL {
            ?individual sxcxcx:r34 ?pchar. # Individual has a Personal_Characteristic
            ?pchar ssx:r11 ?gender. # Gender
            FILTER (?gender != "?")
        }

        # Provide Race, if it exists
        OPTIONAL {
            ?individual sxcxcx:r34 ?pchar. # Individual has a Personal_Characteristic
            ?pchar ssx:r53 ?race. # Race
            FILTER (?race != "?")
        }

        # Provide Quantitative Age, if it exists
        OPTIONAL {
            ?individual sxcxcx:r34 ?pchar. # Individual has a Personal_Characteristic
            ?pchar sxcxcx:r89 ?age. # Personal_Characteristic has an Age
            ?age ssx:r76 ?quantitative_age. # Quantitative Age
            FILTER (?quantitative_age != "?")
        }

        # Provide Last Name, if it exists
        OPTIONAL {
            ?individual sxcxcx:r34 ?pchar. # Individual has a Personal_Characteristic
            ?pchar sxcxcx:r5 ?name. # Personal_Characteristic has an First and Last Name
            ?name ssx:r10 ?lname. # Last Name
            FILTER (?lname != "?")
        }
    }
"""

'Find semantic triplets related to a MacroEvent'
events['triplets']="""
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX scx:<http://galyn.example.com/source_data_files/setup_Complex.csv#>
    PREFIX ssx:<http://galyn.example.com/source_data_files/setup_Simplex.csv#>
    PREFIX sxcxcx:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#>

    SELECT DISTINCT ?triplet ?trlabel ?event ?evlabel ?melabel
    WHERE {
      # First find all the Macro events, all fo the Events for those macros,
      # and all fo the Triplets for those events. 
      ?macro a scx:r1;                    # Macro event
             dcx:Identifier ?melabel;
             sxcxcx:r61 ?event.           # Event
      ?event dcx:Identifier ?evlabel;
             sxcxcx:r62 ?triplet.         # Semantic Triplet
      ?triplet dcx:Identifier ?trlabel.             

    }
    # Order by UCASE to fold case.
    ORDER BY ?event UCASE(?trlabel)
"""

