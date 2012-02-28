from collections import defaultdict
from rdflib import Variable
from urllib import quote

from django.template.defaultfilters import slugify

from georgia_lynchings import query_bank
from georgia_lynchings.rdf.fields import RdfPropertyField, \
    ReversedRdfPropertyField, ChainedRdfPropertyField, UnionRdfPropertyField
from georgia_lynchings.rdf.models import ComplexObject
from georgia_lynchings.rdf.ns import scxn, ssxn, sxcxcxn, ix_ebd, dcx
from georgia_lynchings.rdf.sparql import SelectQuery
from georgia_lynchings.rdf.sparqlstore import SparqlStore
import logging
from pprint import pprint

logger = logging.getLogger(__name__)


class MacroEvent(ComplexObject):
    '''A Macro Event is an object type defined by the project's (currently
    private) PC-ACE database. It represents a lynching case and all of the
    individual events associated with it.
    '''

    rdf_type = scxn.Macro_Event
    'the URI of the RDF Class describing macro event objects'     

    # NOTE: Fields for complex subobjects are defined on the subobjects
    # themselves to simplify syntax. For example, see Event.macro_event,
    # below, which adds an "events" property to MacroEvent with its
    # reverse_field_name.
    
    def index_data(self):
        '''Return a dictionary of index terms for this macro event.
        `sunburnt <http://opensource.timetric.com/sunburnt/>`_ expects a
        dictionary whose keys are solr field names and whose values are the
        values to index for those terms. These values can be single values
        or lists. Lists will be indexed in solr as multi-valued fields.
        '''
        data = super(MacroEvent, self).index_data().copy()
        
        # victims new format (mutliple victims and assoc. properties)
        data['victim_uri'] = []        
        data['victim_name_brundage'] = []
        data['victim_county_brundage'] = []
        data['victim_lynchingdate_brundage'] = []
        data['victim_race_brundage'] = []
        data['victim_allegedcrime_brundage'] = []
        # NOTE: victim age as qualitative_age and exact_age are available
        victim_rows = self.get_victim_data()
        if len(victim_rows) > 1: 
            logger.debug("Multiple [%d] Victims for event[%s]" % (len(victim_rows), victim_rows[0]['macro']))
        for victim_row in victim_rows:
            if 'victim' in victim_row:
                data['victim_uri'].append(victim_row['victim'])            
            if 'vname_brdg' in victim_row:
                data['victim_name_brundage'].append(victim_row['vname_brdg'])
            if 'vcounty_brdg' in victim_row:
                data['victim_county_brundage'].append(victim_row['vcounty_brdg'])
            if 'vlydate_brdg' in victim_row:
                data['victim_lynchingdate_brundage'].append(victim_row['vlydate_brdg'])
            if 'vrace_brdg' in victim_row:
                data['victim_race_brundage'].append(victim_row['vrace_brdg'])
            if 'victim_allegedcrime_brundage' in victim_row:
                data['victim_allegedcrime_brundage'].append(victim_row['victim_allegedcrime_brundage'])

        datedict = self.get_date_range()
        if datedict:
            data['min_date'] = datedict['mindate']
            data['max_date'] = datedict['maxdate']

        details = self.get_details()
        if details:
            data = dict(data.items() + details.items())            

        cities = self.get_cities()
        if cities:
            data['city'] = cities            

        data['triplet_label'] = [row['trlabel'] for row in self.get_triplets()]

        # for self, get all its participants, and prepopulate several fields as
        # part of the query. use these to populate participant index_data
        participants = self.objects.events.triplets.participants.fields(
                'actor_name', 'last_name', 'qualitative_age', 'race', 'gender', 'residence')
        data['participant_uri'] = [part.uri for part in participants]
        data['participant_last_name'] = [part.last_name for part in participants if part.last_name]
        data['participant_qualitative_age'] = [part.qualitative_age for part in participants if part.qualitative_age]
        data['participant_race'] = [part.race for part in participants if part.race]
        data['participant_gender'] = [part.gender for part in participants if part.gender]
        data['participant_actor_name'] = [part.actor_name for part in participants if part.actor_name]
        data['participant_residence'] = [part.residence for part in participants if part.residence]

        return data

    # methods for wrapping a MacroEvent around a URI and querying utility
    # data about it. For now these methods have hard-coded SPARQL, but we
    # hope in time to be able to generate these queries from the RDF
    # properties above.

    #TODO: consider moving the PDF documents to /static/documents so that it can work with runserver and apache
    def get_articles(self, clean=True):
        '''Get all articles associated with this macro event, along with the
        particular events that the articles are attached to.

        :param clean: when True(default) will modify docpath and add docpath_link to make results more html friendly.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It has the following bindings:

                  * `melabel`: the :class:`MacroEvent` label
                  * `event`: the uri of the event associated with this article
                  * `evlabel`: the event label
                  * `dd`: the uri of the article
                  * `docpath`: a relative path to the document data, if clean=True it is changed to the filename only
                  * `docpath_link`:  only present when clean=True, relative path to the document that is quoted and
                    all back slashes have been changed to forward slashes

                The matches are ordered by `event` and `docpath`.
        '''

        query=query_bank.events['articles']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})
        # return the dictionary resultset of the query

        if clean:
            for result in resultSet:
                # Clean up data, add "n/a" if value does not exist
                if 'docpath' in result.keys():
                    # TODO find a better way to do this
                    result['docpath_link'] = quote(result['docpath'].replace('\\', '/'))
                    result['docpath'] = result['docpath'][10:]
        return resultSet
        
    def get_cities(self):
        '''Get all cities associated with this macro event.

        :rtype: a list of city names associated with this macro event,
                expressed as :class:`rdflib.Literal` objects (a subclass of
                ``unicode``)
        '''

        query=query_bank.events['cities']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                                       
        # return the list of cities
        return [result['city'] for result in resultSet]
        
    def get_date_range(self):
        '''Get minimum and maximum date range associated with this macro event.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It has the following bindings:
                  * `mindate`: the minimum date related to this event
                  * `maxdate`: the maximum date related to this event                  
                  * `event`: the uri of the event associated with this article                  
                  * `melabel`: the :class:`MacroEvent` label
                  * `evlabel`: the event label

                The matches are ordered by `event` and `docpath`.
        '''

        query=query_bank.events['date_range']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                                       
        # return a dictionary with min and max keys
        if resultSet:
            datedict = {}        
            for result in resultSet:
                if 'mindate' in result:
                    datedict['mindate']=result['mindate']
                    datedict['maxdate']=result['maxdate']
                else: return None
            return datedict
        else: return None
        
    def get_details(self):
        '''Get all details associated with this macro event.

        :rtype: a mapping list of the type 
                It has the following bindings:               
                  * `melabel`: the :class:`MacroEvent` label
                  * `event`: the uri of the event associated with this article                  
                  * `evlabel`: the event label
                  * `event_type`: the event type
                  * `outcome`: the name of the outcome                  
                  * `reason`: the name of the reason
        '''                
        query=query_bank.events['details']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})

        detailResult={}
        # return a unique list of event_types, reasons and outcomes
        for item in ['event_type', 'reason', 'outcome']:
            try:
                detailResult[item] = set([result[item] for result in resultSet])
            except:
                logger.debug("%s is not defined for macro event %s" % (item, self.uri.n3()))

        # return the list of cities
        return detailResult  
                
    def get_events(self):
        '''Get the events associated with this macro event.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It has the following bindings:               
                  * `melabel`: the :class:`MacroEvent` label
                  * `event`: the uri of the event associated with this article                  
                  * `evlabel`: the event label
        '''                
        query=query_bank.events['macro']
        ss=SparqlStore()
        results = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})

        # return the dictionary results of the details information          
        return results
        
    def get_triplets(self):
        '''Get the semantic triplets related to this macro event.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It returns one row per triplet associated with this Macro
                Event, with the following bindings:
                  * `triplet`: the URI of the triplet
                  * `trlabel`: the label of the triplet
                  * `event`: the URI of the Event containing the triplet
                  * `evlabel`: the label of that Event
                  * `melabel`: the label of this Macro Event

                The matches are ordered by `event` and case-folded
                `trlabel`.
        '''
        query=query_bank.events['triplets']
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                                       
        return resultSet

    def get_triplets_by_event(self):
        triplets = self.get_triplets()
        events = defaultdict(list)
        for triplet in triplets:
            events[triplet['evlabel']].append(triplet['trlabel'])
        return events

    # Get unique participant (of type subject or object) data
    def get_statement_data(self, stmt_type):
        '''Get unique data about the particpant (sentence object or subject) 
        of statements related to this macro event.
        
        :param stmt_type: a type of participant 'uparto' or 'uparts' for
                unique participant subject or object.        

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
                It has the following bindings:
                  * `fname`: fname of this actor                 
                  * `lname`: lname of this actor 
                  * `qualitative_age`: qualitative_age of this actor                                   
                  * `race`: race of this actor 
                  * `gender`: gender of this actor 
                  * `name_of_indivd_actor`: Name of Individual Actor              
                  * `event`: the uri of the event associated with this article                  
                  * `melabel`: the :class:`MacroEvent` label
                  * `evlabel`: the event label
                  * `macro`: the macro event ID
        '''

        query=query_bank.events[stmt_type]
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query, 
                             initial_bindings={'macro': self.uri.n3()})                                       
        # return a dictionary of the resultSet
        return resultSet        
        
    def get_victim_data(self):
        '''Get the victim data related to this macro event.

        :rtype: a mapping list of the type returned by
                :meth:`~georgia_lynchings.rdf.sparqlstore.SparqlStore.query`.
                It returns one row per victim associated with this Macro
                Event, with the following bindings:              
                  * `vname_brdg`: the (Brundage) name of the Victim
                  * `vcounty_brdg`: the (Brundage) county of the Victim
                  * `vallegedcrime_brdg`: the (Brundage) alleged crime of the Victim
                  * `vlydate_brdg`: the (Brundage) lynching date of the Victim
                  * `vrace_brdg`: the (Brundage) race of the Victim                                                                       
                  * `victim`: the URI of the Victim
                  * `macro`: the URI of this Macro Event
        '''
        store = SparqlStore()
        resultSet = store.query(sparql_query=get_victim_query(), 
                             initial_bindings={'macro': self.uri.n3()})
        return resultSet        

def get_all_macro_events():
    '''Get a list of macro events along with number of linked articles.

    :rtype: a mapping list of the type returned by
            :meth:`~georgia_lynchings.events.sparqlstore.SparqlStore.query`.
            It has the following bindings:

              * `macro`: the uri of the associated macro event
              * `melabel`: the macro event label
              * `articleTotal`: article count.

    '''
    query=query_bank.events['all']    
    ss=SparqlStore()
    resultSet = ss.query(sparql_query=query)
    # create a link for the macro event articles
    for result in resultSet:
        row_id = result['macro'].split('#r')[1]
        result['details_link'] = '%s/details' % row_id        
        result['articles_link'] = '%s/articles' % row_id
    # return the dictionary resultset of the query          
    return resultSet
    
def get_victim_query():
    '''Get the query to retrieve victim information.

    :rtype: a unicode string of the SPARQL query

    '''
    q = SelectQuery(results=['macro', 'victim', 'vname_brdg', \
        'vlydate_brdg', 'vcounty_brdg', 'victim_allegedcrime_brundage'])
    q.append((Variable('macro'), sxcxcxn.Victim, Variable('victim')))
    q.append((Variable('victim'), sxcxcxn.Victim_Brundage, Variable('victim_Brundage')))   
    q.append((Variable('victim_Brundage'), ssxn.Date_of_lynching_Brundage, \
        Variable('vlydate_brdg')), optional=True)
    q.append((Variable('victim_Brundage'), ssxn.County_of_lynching_Brundage, \
        Variable('vcounty_brdg')), optional=True)
    q.append((Variable('victim_Brundage'), ssxn.Alleged_crime_Brundage, \
        Variable('victim_allegedcrime_brundage')), optional=True)
    q.append((Variable('victim_Brundage'), ssxn.Name_of_victim_Brundage, \
        Variable('vname_brdg')), optional=True)
    q.append((Variable('victim_Brundage'), ssxn.Race_Brundage, \
        Variable('vrace_brdg')), optional=True)

    return unicode(q)  
    
def get_metadata_query():
    '''Get the query to retrieve core metadata information.

    :rtype: a unicode string of the SPARQL query

    '''
    q = SelectQuery(results=['macro', 'label', 'min_date', 'max_date', \
        'vcounty_brdg'], distinct=True)
    q.append((Variable('macro'), sxcxcxn.Event, Variable('event')))
    q.append((Variable('macro'), dcx.Identifier, Variable('label')))  
    q.append((Variable('event'), ix_ebd.mindate, Variable('min_date')))
    q.append((Variable('event'), ix_ebd.maxdate, Variable('max_date')))
    q.append((Variable('macro'), sxcxcxn.Victim, Variable('victim')))
    q.append((Variable('victim'), sxcxcxn.Victim_Brundage, Variable('victim_Brundage')))     
    q.append((Variable('victim_Brundage'), ssxn.County_of_lynching_Brundage, \
            Variable('vcounty_brdg')))
    return unicode(q)
    
def get_metadata(add_fields=[]):
    '''Get the macro event core metadata from sesame triplestore, plus
    any additional fields used in the timemap filter.
    
    :param add_fields: add extra fields to the basic metadata set.    

    :rtype: a mapping dict of core metadata plus timemap field using
            core data returned by
            :meth:`~georgia_lynchings.rdf.sparqlstore.SparqlStore.query`.
            joined with data from additional filter fields, and indexed
            on the macro event id.
            with the following bindings:
              * `label`: the label of this Macro Event              
              * `min_date`: the minimum date related to this event
              * `max_date`: the maximum date related to this event
              * `victim_county_brundage`: the (Brundage) county of the Victim
              plus any additional fields used by the timemap filter
    '''
    store = SparqlStore()
    resultSet = store.query(sparql_query=get_metadata_query())
    
    resultSetIndexed = indexOnMacroEvent(resultSet)
    
    # Add any additional field requests
    update_filter_fields(add_fields, resultSetIndexed)
    
    return resultSetIndexed
    
def indexOnMacroEvent(resultSet=[]):
    '''Create a new dictionary using the macroevent id as the key.
    
    :param resultSet: a mapping list of the type returned by
            :meth:`~georgia_lynchings.rdf.sparqlstore.SparqlStore.query`.
            It returns metadata for all  MacroEvents, 
            with the following bindings:
              * `macro`: the URI of this Macro Event
              * `label`: the label of this Macro Event              
              * `min_date`: the minimum date related to this event
              * `max_date`: the maximum date related to this event
              * `victim_county_brundage`: the (Brundage) county of the Victim
              
    :rtype: a mapping dictionary of the resultSet using the macroevent 
            id as the key.           
    '''
    indexedResultSet = {}
    if resultSet:
        fields = resultSet[0].keys()
        fields.remove('macro')        
        for item in resultSet:
            row_id = item['macro'].split('#r')[1]
            del item['macro']
            indexedResultSet[row_id]=item

    return indexedResultSet
    
def update_filter_fields(add_fields=[], resultSetIndexed={}):
    '''Update the core metadata with filter field data.
    
    :param add_fields: add extra fields to the basic metadata set.    

    :param resultSetIndexed: a mapping dict of core metadata using the
        macroevent id as the dict key.  
    '''

    # Add `victim_allegedcrime_brundage`, if present in add_fields list
    if 'victim_allegedcrime_brundage' in add_fields:
        q = SelectQuery(results=['macro', 'victim_allegedcrime_brundage'], distinct=True)
        q.append((Variable('macro'), sxcxcxn.Victim, Variable('victim')))
        q.append((Variable('victim'), sxcxcxn.Victim_Brundage, Variable('victim_Brundage')))  
        q.append((Variable('victim_Brundage'), ssxn.Alleged_crime_Brundage, \
                Variable('victim_allegedcrime_brundage')))              
        store = SparqlStore()
        ac_resultSet = store.query(sparql_query=unicode(q))
        join_data_on_macroevent(resultSetIndexed, ac_resultSet)

    # Add `cities`, if present in add_fields list
    if 'city' in add_fields:
        query=query_bank.filters['city']    
        ss=SparqlStore()
        city_resultSet = ss.query(sparql_query=query)
        join_data_on_macroevent(resultSetIndexed, city_resultSet)
                
def join_data_on_macroevent(resultSetIndexed={}, filterdict=[]):
    '''Join the filter resultSet to the metadata indexed dictionary  

    :param resultSetIndexed: a mapping dict of core metadata using the
        macroevent id as the dict key. 
    :param filterdict: a list of dictionary with the following bindings:
              * `macro`: the URI of this Macro Event
              * filtername: the name of the filter 
    '''
    if resultSetIndexed and filterdict:
        filtername = filterdict[0].keys()
        filtername.remove('macro')
        filtername = filtername[0]
        for item in filterdict:
            try:
                row_id = item['macro'].split('#r')[1]
                if filtername in resultSetIndexed[row_id]:
                    if item[filtername] not in resultSetIndexed[row_id][filtername]:
                        resultSetIndexed[row_id][filtername].append(item[filtername].encode('ascii').title())
                else:
                    resultSetIndexed[row_id][filtername] = [item[filtername].encode('ascii').title()]
            except KeyError, err:
                logger.debug("Filter[%s] not defined for MacroEvent[%s]" % (filtername, err))
    
def get_filters(filters):
    '''Get the queries to retrieve filters tags and frequency.

    :param filter: a mapping dict of the timemap filters.
            It has the following bindings:
              * `title`: the display name of the filter tag
              * `name`: the filter name
              * `prefix`: the prefix to the slug value
              
    :rtype: an updated mapping dict of the timemap filters.
            It has the following bindings:
              * `title`: the display name of the filter tag
              * `name`: the filter name
              * `prefix`: the prefix to the slug value
              * `tags`: a tuple as (filtername, slug, frequency)
    '''

    for filter in filters:
        query=query_bank.filters[filter['name']+"_freq" ]  
        ss=SparqlStore()
        resultSet = ss.query(sparql_query=query)

        tag_tuples = []
        # Add tags and frequency as tuples to filter dict
        for item in resultSet:
            # Slugify the tag (lc, add prefix, replace spaces with underscore.
            slug = slugify(filter['prefix'] + " " + item[filter['name']])
            tag_tuples.append((item[filter['name']],slug,item['frequency']))

        filter['tags'] = tag_tuples           
         
    return filters  

class Event(ComplexObject):
    '''An Event is an object type defined by the project's private PC-ACE
    database. It represents a particular news story within a lynching case
    and all of the individual semantic triplets associated with it.
    '''

    rdf_type = scxn.Event
    'the URI of the RDF Class describing event objects'

    # complex fields potentially attached to an Event
    space = sxcxcxn.Space
    'a place associated with this event'

    # simplex fields potentially attached to an Event
    event_type = ssxn.Type_of_event
    'a word or short phrase describing the type of event'

    # reverse and aggregate properties
    macro_event = ReversedRdfPropertyField(sxcxcxn.Event,
                                           result_type=MacroEvent,
                                           reverse_field_name='events')


class SemanticTriplet(ComplexObject):
    '''A Semantic Triplet is an object type defined by the project's private
    PC-ACE database. It represents a single statement encoded from a news
    article.
    '''

    rdf_type = scxn.Semantic_Triplet
    'the URI of the RDF Class describing semantic triplet objects'

    # complex fields potentially attached to a Semantic Triplet
    process = sxcxcxn.Process
    'the verb of the statement'
    alternative = sxcxcxn.Alternative_triplet
    'an alternate and potentially conflicting rendition of this triplet'

    # simplex fields potentially attached to a Semantic Triplet
    relation_to_next = ssxn.Relation_to_next_triplet
    'conjunction or subordinating phrase linking this triplet to the next'
    is_passive = ssxn.Passive_no_agent
    'does the statement use passive voice? (typically specified only if true)'

    # reverse and aggregate properties
    event = ReversedRdfPropertyField(sxcxcxn.Semantic_Triplet,
                                     result_type=Event, 
                                     reverse_field_name='triplets')
    macro_event = ChainedRdfPropertyField(event, Event.macro_event)

    def index_data(self):
        data = super(SemanticTriplet, self).index_data().copy()

        macro_event = self.macro_event
        if macro_event:
            data['macro_event_uri'] = macro_event.uri

        return data


class Participant(ComplexObject):
    triplet = ReversedRdfPropertyField(UnionRdfPropertyField(sxcxcxn.Participant_S,
                                                             sxcxcxn.Participant_O),
                                       result_type=SemanticTriplet,
                                       reverse_field_name='participants')

    actor_name = ChainedRdfPropertyField(sxcxcxn.Actor, sxcxcxn.Individual,
                                         ssxn.Name_of_individual_actor)
    last_name = ChainedRdfPropertyField(sxcxcxn.Actor, sxcxcxn.Individual,
                                        sxcxcxn.Personal_characteristics,
                                        sxcxcxn.First_name_and_last_name,
                                        ssxn.Last_name)
    qualitative_age = ChainedRdfPropertyField(sxcxcxn.Actor, sxcxcxn.Individual,
                                              sxcxcxn.Personal_characteristics,
                                              sxcxcxn.Age,
                                              ssxn.Qualitative_age)
    race = ChainedRdfPropertyField(sxcxcxn.Actor, sxcxcxn.Individual,
                                   sxcxcxn.Personal_characteristics,
                                   ssxn.Race)
    gender = ChainedRdfPropertyField(sxcxcxn.Actor, sxcxcxn.Individual,
                                     sxcxcxn.Personal_characteristics,
                                     ssxn.Gender)
    residence = ChainedRdfPropertyField(sxcxcxn.Actor, sxcxcxn.Individual,
                                        sxcxcxn.Personal_characteristics,
                                        sxcxcxn.Residence, dcx.Identifier)
    

class Participant_S(Participant):
    rdf_type = scxn.Participant_S
    triplet_with_subject = ReversedRdfPropertyField(RdfPropertyField(sxcxcxn.Participant_S),
                                                    result_type=SemanticTriplet,
                                                    reverse_field_name='participant_s')

class Participant_O(Participant):
    rdf_type = scxn.Participant_O
    triplet_with_object = ReversedRdfPropertyField(RdfPropertyField(sxcxcxn.Participant_O),
                                                   result_type=SemanticTriplet,
                                                   reverse_field_name='participant_o')


class Victim(ComplexObject):
    '''A Victim is an object type defined by the project's private
    PC-ACE database. It represents a Victim Grouping of a Macro Event and 
    several properties associated with it.
    '''

    rdf_type = scxn.Victim
    'the URI of the RDF Class describing victim objects'
    
    # simplex fields potentially attached to a Victim
    # Victim has a name (Brundage)
    victim_uri = sxcxcxn.Victim
    
    # simplex fields potentially attached to a Victim
    # Victim has a name (Brundage)
    #victim_name = ssxn.Name_of_victim_Brundage
    
    victim_name = ChainedRdfPropertyField(sxcxcxn.Victim_Brundage,
                                        ssxn.Name_of_victim_Brundage)    

    # Victim has a county of lynching (Brundage)
    victim_county_of_lynching = ChainedRdfPropertyField(sxcxcxn.Victim_Brundage,
                                        ssxn.County_of_lynching_Brundage) 
                                                
    # Victim has an alleged crime (Brundage)        
    victim_alleged_crime = ChainedRdfPropertyField(sxcxcxn.Victim_Brundage,
                                        ssxn.Alleged_crime_Brundage)    
    
    # Victim has a date of lynchings (Brundage)    
    victim_date_of_lynching = ChainedRdfPropertyField(sxcxcxn.Victim_Brundage,
                                        ssxn.Date_of_lynching_Brundage)     
    
    # Victim has a race (Brundage)    
    victim_race = ChainedRdfPropertyField(sxcxcxn.Victim_Brundage,
                                        ssxn.Race_Brundage)       
                    
    # reverse and aggregate properties
    macro_event = ReversedRdfPropertyField(sxcxcxn.Victim,
                                           result_type=MacroEvent,
                                           reverse_field_name='victims')

    def index_data(self):
        data = super(Victim, self).index_data().copy()

        macro_event = self.macro_event
        if macro_event:
            data['macro_event_uri'] = macro_event.uri

        return data
