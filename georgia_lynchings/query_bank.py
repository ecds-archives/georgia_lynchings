'''
This file contains a dictionary of predefined SPARQL queries.
'''

articles={}
events={}
filters={}

articles['all']="""
    prefix dd: <http://galyn.example.com/source_data_files/data_Document.csv#>
    prefix ssxn: <http://galyn.example.com/source_data_files/setup_Simplex.csv#name->

    select ?id ?paperdate ?papername ?articlepage ?docpath where {
        ?dd a dd:Row;
            dd:ID ?id.
        optional { ?dd ssxn:Newspaper_date ?paperdate }
        optional { ?dd ssxn:Newspaper_name ?papername }
        optional { ?dd ssxn:Page_number ?articlepage }
        optional { ?dd ssxn:documentPath ?docpath }
    }
"""

'Find articles related to a MacroEvent'
events['articles']="""
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX dxcxd:<http://galyn.example.com/source_data_files/data_xref_Complex-Document.csv#>
    PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
    PREFIX ssxn:<http://galyn.example.com/source_data_files/setup_Simplex.csv#name->
    PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->

    SELECT DISTINCT ?melabel ?event ?evlabel ?dd ?docpath ?paperdate ?papername ?articlepage
    WHERE {
      # First find all of the Macro events and all of the Events for those
      # Macros. Macros aren't strictly necessary, but they're provided
      # here for
      # context.
      ?macro a scxn:Macro_Event;
             dcx:Identifier ?melabel;
             sxcxcxn:Event ?event.
      ?event dcx:Identifier ?evlabel.

      # Report URI and file path of each document for the event
      ?dxcxd dxcxd:Complex ?event;
             dxcxd:Document ?dd.
      optional { ?dd ssxn:Newspaper_date ?paperdate }
      optional { ?dd ssxn:Newspaper_name ?papername }
      optional { ?dd ssxn:Page_number ?articlepage }
      optional { ?dd ssxn:documentPath ?docpath }              
                    }
    ORDER BY ?event ?docpath
"""

'Find cities related to a Macro Event'
events['cities']="""
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
    PREFIX ssxn:<http://galyn.example.com/source_data_files/setup_Simplex.csv#name->
    PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->

    SELECT DISTINCT ?city
    WHERE {
      # For a pre-bound ?macro (or for all Macro Events), find all of the
      # Events for those macros, and all of the Triplets for those events.
      # We'll be looking in these triplets for locations.

      ?macro a scxn:Macro_Event;
             dcx:Identifier ?melabel;
             sxcxcxn:Event ?event.
      ?event dcx:Identifier ?evlabel;
             sxcxcxn:Semantic_Triplet ?_1.

      # Every Triplet has a Process
      ?_1 sxcxcxn:Process ?_2.

      # We need all of the places for that Process. There are four ways
      # they might be expressed:
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

      # Regardless of which way we came, ?_5 is some sort of place. If
      # we're going to get from there to location simplex data, this
      # is how we get there:
      {
        ?_5 sxcxcxn:City ?_10.
      }

      # Grab the simplex data we're interested in, whichever are
      # available (but note that "?" is equivalent to missing data)
      OPTIONAL {
        ?_10 ssxn:City_name ?city.
        FILTER (?city != "?")
      }

      # And grab only those records that have at least one data point.
      FILTER (BOUND(?city))
    }
"""

'Find date range for a MacroEvent'
events['date_range'] = """
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
    PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->
    PREFIX ix_ebd:<http://galyn.example.com/constructed_statements/index/events_by_date/#>

    SELECT ?macro ?melabel ?event ?evlabel ?mindate ?maxdate
    WHERE {
      ?macro a scxn:Macro_Event;                  
             dcx:Identifier ?melabel;
             sxcxcxn:Event ?event.         
      ?event dcx:Identifier ?evlabel;
             ix_ebd:mindate ?mindate;
             ix_ebd:maxdate ?maxdate.
    }
    ORDER BY ?mindate
"""


'Find details related to a Macro Event'
events['details']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
PREFIX ssxn:<http://galyn.example.com/source_data_files/setup_Simplex.csv#name->
PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->

SELECT DISTINCT ?macro ?melabel ?event ?evlabel ?event_type ?outcome ?reason   
WHERE {
    # First find all the Macro events, and all the Events for those macros,
    # and the type_of_event, type of event, name of reason, and name of outcome.
    ?macro a scxn:Macro_Event; # Macro event
        dcx:Identifier ?melabel;
        sxcxcxn:Event ?event. # Event
    ?event dcx:Identifier ?evlabel;
    
    OPTIONAL {
        ?event ssxn:Type_of_event ?event_type.
        FILTER (?event_type != "?")
    }
    
            
    OPTIONAL {
        ?event dcx:Identifier ?evlabel;
             sxcxcxn:Semantic_Triplet ?_1.
        # Every Triplet has a Process
        ?_1 sxcxcxn:Process ?_2.
        ?_2 sxcxcxn:Simple_process ?_3.
        ?_3 sxcxcxn:Circumstances ?_4.
        ?_4 sxcxcxn:Outcome ?_5.
        ?_4 sxcxcxn:Reason ?_6.
      
      OPTIONAL {
        ?_5 ssxn:Name_of_outcome ?outcome.
        FILTER (?outcome != "?")
      } 
      
      OPTIONAL {
        ?_6 ssxn:Name_of_reason ?reason.
        FILTER (?reason != "?")
      }
    }
}
ORDER BY ?macro
"""

'Find all Macro Events'
events['macro']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->

SELECT DISTINCT ?macro ?melabel ?event ?evlabel
WHERE {
  ?macro a scxn:Macro_Event;
  OPTIONAL { ?macro dcx:Identifier ?melabel. }
  ?macro sxcxcxn:Event ?event.
  ?event dcx:Identifier ?evlabel.  
}
ORDER BY ?macro
"""

'Find all Macro Events Documents'
events['all']="""
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX dxcxd:<http://galyn.example.com/source_data_files/data_xref_Complex-Document.csv#>
    PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
    PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->

    SELECT ?macro ?melabel (COUNT(?dd) AS ?articleTotal)
    WHERE {
      ?macro a scxn:Macro_Event;
             dcx:Identifier ?melabel;
             sxcxcxn:Event ?event.
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
PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
PREFIX ssxn:<http://galyn.example.com/source_data_files/setup_Simplex.csv#name->
PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->

SELECT DISTINCT ?fname ?lname ?qualitative_age ?race ?gender ?name_of_indivd_actor ?individual ?parto ?actor ?event ?evlabel ?melabel ?macro
WHERE {
    # First find all the Macro events, and all the Events for those macros,
    # and all of the Triplets for those events, and all the Participant-O
    # for each triplet. We'll be looking in these for detail information.
    ?macro a scxn:Macro_Event;
        dcx:Identifier ?melabel;
        sxcxcxn:Event ?event.
    ?event dcx:Identifier ?evlabel;
        sxcxcxn:Semantic_Triplet ?_1.
    # Every Triplet has a Participant-O
    ?_1 sxcxcxn:Participant_O ?parto.

    # We need all of the individuals for that Semantic Triplet.
    {
        ?parto sxcxcxn:Actor ?actor.
        ?actor sxcxcxn:Individual ?individual.
    }

    # Provide Name_of_individual_actor, if it exists
    OPTIONAL {
        ?individual ssxn:Name_of_individual_actor ?name_of_indivd_actor.
        FILTER (?name_of_indivd_actor != "?")
    }

    # Provide Gender, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar ssxn:Gender ?gender.
        FILTER (?gender != "?")
    }

    # Provide Race, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar ssxn:Race ?race.
        FILTER (?race != "?")
    }

    # Provide Qualitative Age, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar sxcxcxn:Age ?age.
        ?age ssxn:Qualitative_age ?qualitative_age.
        FILTER (?qualitative_age != "?")
    }
    
    # Provide First Name, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar sxcxcxn:First_name_and_last_name ?name.
        ?name ssxn:First_name ?fname.
        FILTER (?fname != "?")
    }        

    # Provide Last Name, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar sxcxcxn:First_name_and_last_name ?name.
        ?name ssxn:Last_name ?lname.
        FILTER (?lname != "?")
    }
}
"""

'Find unique detail information about Participant-O Actor'
events['uparto']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
PREFIX ssxn:<http://galyn.example.com/source_data_files/setup_Simplex.csv#name->
PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->

SELECT DISTINCT ?fname ?lname ?qualitative_age ?race ?gender ?name_of_indivd_actor ?event ?evlabel ?melabel ?macro ?occupation
WHERE {
    # First find all the Macro events, and all the Events for those macros,
    # and all of the Triplets for those events, and all the Participant-O
    # for each triplet. We'll be looking in these for detail information.
    ?macro a scxn:Macro_Event;
        dcx:Identifier ?melabel;
        sxcxcxn:Event ?event.
    ?event dcx:Identifier ?evlabel;
        sxcxcxn:Semantic_Triplet ?_1.
    # Every Triplet has a Participant-O
    ?_1 sxcxcxn:Participant_O ?parto.

    # We need all of the individuals for that Semantic Triplet.
    {
        ?parto sxcxcxn:Actor ?actor.
        ?actor sxcxcxn:Individual ?individual.
    }

    # Provide Name_of_individual_actor, if it exists
    OPTIONAL {
        ?individual ssxn:Name_of_individual_actor ?name_of_indivd_actor.
        FILTER (?name_of_indivd_actor != "?")
    }

    # Provide Gender, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar ssxn:Gender ?gender.
        FILTER (?gender != "?")
    }

    # Provide Race, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar ssxn:Race ?race.
        FILTER (?race != "?")
    }

    # Provide Qualitative Age, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar sxcxcxn:Age ?age.
        ?age ssxn:Qualitative_age ?qualitative_age.
        FILTER (?qualitative_age != "?")
    }
    
    # Provide First Name, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar sxcxcxn:First_name_and_last_name ?name.
        ?name ssxn:First_name ?fname.
        FILTER (?fname != "?")
    }        

    # Provide Last Name, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar sxcxcxn:First_name_and_last_name ?name.
        ?name ssxn:Last_name ?lname.
        FILTER (?lname != "?")
    }

    # Provide Occupation, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar ssxn:Occupation ?occupation.
        FILTER (?occupation != "?")
    }
}
"""


'Find detail information about Participant-S Actor'
events['parts']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
PREFIX ssxn:<http://galyn.example.com/source_data_files/setup_Simplex.csv#name->
PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->

SELECT DISTINCT ?fname ?lname ?qualitative_age ?race ?gender ?name_of_indivd_actor ?individual ?parts ?actor ?event ?evlabel ?melabel ?macro
WHERE {
    # First find all the Macro events, and all the Events for those macros,
    # and all of the Triplets for those events, and all the Participant-S
    # for each triplet. We'll be looking in these for detail information.
    ?macro a scxn:Macro_Event;
        dcx:Identifier ?melabel;
        sxcxcxn:Event ?event.
    ?event dcx:Identifier ?evlabel;
        sxcxcxn:Semantic_Triplet ?_1.
    # Every Triplet has a Participant-S
    ?_1 sxcxcxn:Participant_S ?parto.

    # We need all of the individuals for that Semantic Triplet.
    {
        ?parto sxcxcxn:Actor ?actor.
        ?actor sxcxcxn:Individual ?individual.
    }

    # Provide Name_of_individual_actor, if it exists
    OPTIONAL {
        ?individual ssxn:Name_of_individual_actor ?name_of_indivd_actor.
        FILTER (?name_of_indivd_actor != "?")
    }

    # Provide Gender, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar ssxn:Gender ?gender.
        FILTER (?gender != "?")
    }

    # Provide Race, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar ssxn:Race ?race.
        FILTER (?race != "?")
    }

    # Provide Qualitative Age, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar sxcxcxn:Age ?age.
        ?age ssxn:Qualitative_age ?qualitative_age.
        FILTER (?qualitative_age != "?")
    }

    # Provide First Name, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar sxcxcxn:First_name_and_last_name ?name.
        ?name ssxn:First_name ?fname.
        FILTER (?fname != "?")
    }

    # Provide Last Name, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar sxcxcxn:First_name_and_last_name ?name.
        ?name ssxn:Last_name ?lname.
        FILTER (?lname != "?")
    }
}

"""

'Find uniquedetail information about Participant-S Actor'
events['uparts']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
PREFIX ssxn:<http://galyn.example.com/source_data_files/setup_Simplex.csv#name->
PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->

SELECT DISTINCT ?fname ?lname ?qualitative_age ?race ?gender ?name_of_indivd_actor ?event ?evlabel ?melabel ?macro  ?occupation
WHERE {
    # First find all the Macro events, and all the Events for those macros,
    # and all of the Triplets for those events, and all the Participant-S
    # for each triplet. We'll be looking in these for detail information.
    ?macro a scxn:Macro_Event;
        dcx:Identifier ?melabel;
        sxcxcxn:Event ?event.
    ?event dcx:Identifier ?evlabel;
        sxcxcxn:Semantic_Triplet ?_1.
    # Every Triplet has a Participant-S
    ?_1 sxcxcxn:Participant_S ?parto.

    # We need all of the individuals for that Semantic Triplet.
    {
        ?parto sxcxcxn:Actor ?actor.
        ?actor sxcxcxn:Individual ?individual.
    }

    # Provide Name_of_individual_actor, if it exists
    OPTIONAL {
        ?individual ssxn:Name_of_individual_actor ?name_of_indivd_actor.
        FILTER (?name_of_indivd_actor != "?")
    }

    # Provide Gender, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar ssxn:Gender ?gender.
        FILTER (?gender != "?")
    }

    # Provide Race, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar ssxn:Race ?race.
        FILTER (?race != "?")
    }

    # Provide Qualitative Age, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar sxcxcxn:Age ?age.
        ?age ssxn:Qualitative_age ?qualitative_age.
        FILTER (?qualitative_age != "?")
    }

    # Provide First Name, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar sxcxcxn:First_name_and_last_name ?name.
        ?name ssxn:First_name ?fname.
        FILTER (?fname != "?")
    }

    # Provide Last Name, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar sxcxcxn:First_name_and_last_name ?name.
        ?name ssxn:Last_name ?lname.
        FILTER (?lname != "?")
    }

    # Provide Occupation, if it exists
    OPTIONAL {
        ?individual sxcxcxn:Personal_characteristics ?pchar.
        ?pchar ssxn:Occupation ?occupation.
        FILTER (?occupation != "?")
    }
}

"""

'Find semantic triplets related to a MacroEvent'
events['triplets']="""
    PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
    PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
    PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->

    SELECT DISTINCT ?triplet ?trlabel ?event ?evlabel ?melabel
    WHERE {
      # First find all the Macro events, all fo the Events for those macros,
      # and all fo the Triplets for those events. 
      ?macro a scxn:Macro_Event;
             dcx:Identifier ?melabel;
             sxcxcxn:Event ?event.
      ?event dcx:Identifier ?evlabel;
             sxcxcxn:Semantic_Triplet ?triplet.
      ?triplet dcx:Identifier ?trlabel.             
    }
    # Order by UCASE to fold case.
    ORDER BY ?event UCASE(?trlabel)
"""


'Find filter count for alleged crime'
filters['victim_allegedcrime_brundage_freq']="""
SELECT ?victim_allegedcrime_brundage (COUNT(?victim_allegedcrime_brundage) AS ?frequency)
WHERE { 
?macro <http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name-Event> ?event .  
?macro <http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name-Victim> ?victim . 
?victim <http://galyn.example.com/source_data_files/setup_Simplex.csv#name-Alleged_crime_Brundage> ?victim_allegedcrime_brundage . 
}
GROUP BY ?victim_allegedcrime_brundage
ORDER BY DESC(?frequency)
"""

'Find the cities for all the macroevents.'
filters['city']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
PREFIX ssxn:<http://galyn.example.com/source_data_files/setup_Simplex.csv#name->
PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->

SELECT DISTINCT ?macro ?city
WHERE {
  # For all ?macro, find all of the
  # Events for those macros, and all of the Triplets for those events.
  # We'll be looking in these triplets for locations.

  ?macro a scxn:Macro_Event.
  ?macro sxcxcxn:Event ?event.
  ?event sxcxcxn:Semantic_Triplet ?_1.

  # Every Triplet has a Process
  ?_1 sxcxcxn:Process ?_2.

  # We need all of the places for that Process. There are four ways
  # they might be expressed:
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

  # Regardless of which way we came, ?_5 is some sort of place. If
  # we're going to get from there to location simplex data, this
  # is how we get there:
  {
    ?_5 sxcxcxn:City ?_10.
  }

  # Grab the simplex data we're interested in, whichever are
  # available (but note that "?" is equivalent to missing data)
  OPTIONAL {
    ?_10 ssxn:City_name ?city.
    FILTER (?city != "?")
  }

  # And grab only those records that have at least one data point.
  FILTER (BOUND(?city))
}
ORDER BY ?macro
"""

'Find the city and frequency list'
filters['city_freq']="""
PREFIX dcx:<http://galyn.example.com/source_data_files/data_Complex.csv#>
PREFIX scxn:<http://galyn.example.com/source_data_files/setup_Complex.csv#name->
PREFIX ssxn:<http://galyn.example.com/source_data_files/setup_Simplex.csv#name->
PREFIX sxcxcxn:<http://galyn.example.com/source_data_files/setup_xref_Complex-Complex.csv#name->

SELECT DISTINCT ?city (COUNT(?city) AS ?frequency)
WHERE {
  # For a pre-bound ?macro (or for all Macro Events), find all of the
  # Events for those macros, and all of the Triplets for those events.
  # We'll be looking in these triplets for locations.

  ?macro a scxn:Macro_Event;
         dcx:Identifier ?melabel;
         sxcxcxn:Event ?event.
  ?event dcx:Identifier ?evlabel;
         sxcxcxn:Semantic_Triplet ?_1.

  # Every Triplet has a Process
  ?_1 sxcxcxn:Process ?_2.

  # We need all of the places for that Process. There are four ways
  # they might be expressed:
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

  # Regardless of which way we came, ?_5 is some sort of place. If
  # we're going to get from there to location simplex data, this
  # is how we get there:
  {
    ?_5 sxcxcxn:City ?_10.
  }

  # Grab the simplex data we're interested in, whichever are
  # available (but note that "?" is equivalent to missing data)
  OPTIONAL {
    ?_10 ssxn:City_name ?city.
    FILTER (?city != "?")
  }

  # And grab only those records that have at least one data point.
  FILTER (BOUND(?city))
}
GROUP BY ?city
ORDER BY DESC(?frequency)
LIMIT 20
"""
