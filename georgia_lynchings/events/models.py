from collections import defaultdict
from rdflib import Variable
from urllib import quote

from django.db.models import permalink
from django.template.defaultfilters import slugify

from georgia_lynchings import query_bank
from georgia_lynchings.rdf.fields import RdfPropertyField, \
    ReversedRdfPropertyField, ChainedRdfPropertyField, UnionRdfPropertyField
from georgia_lynchings.rdf.models import ComplexObject
from georgia_lynchings.rdf.ns import scxn, ssxn, sxcxcxn, ix_mbd, dcx
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

    start_date = ix_mbd.mindate
    'the earliest date associated with this macro event'
    end_date = ix_mbd.maxdate
    'the latest date associated with this macro event'
    
    @permalink
    def get_absolute_url(self):
        return ('events:details', [str(self.id)])

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

        if self.start_date:
            data['min_date'] = self.start_date
        if self.end_date:
            data['max_date'] = self.end_date

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

    # FIXME: this property is ridiculously complicated. before we use it
    # agat (we're not as of 2012-04-05) we need to either break it up or
    # index it in setup-queries
    city = ChainedRdfPropertyField(process, 
               UnionRdfPropertyField(
                   ChainedRdfPropertyField(
                       sxcxcxn.Simple_process,
                       sxcxcxn.Circumstances,
                       sxcxcxn.Space
                   ),
                   ChainedRdfPropertyField(
                       sxcxcxn.Complex_process,
                       sxcxcxn.Simple_process,
                       sxcxcxn.Circumstances,
                       sxcxcxn.Space
                   ),
                   ChainedRdfPropertyField(
                       sxcxcxn.Complex_process,
                       sxcxcxn.Other_process,
                       sxcxcxn.Simple_process,
                       sxcxcxn.Circumstances,
                       sxcxcxn.Space
                   ),
                   ChainedRdfPropertyField(
                       sxcxcxn.Complex_process,
                       sxcxcxn.Other_process,
                       sxcxcxn.Nominalization,
                       sxcxcxn.Space
                   ),
                   multiple=False
               ),
               sxcxcxn.City,
               ssxn.City_name
           )
    'the city this triplet happened in'

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

    name = ssxn.Name_of_victim
    'name of this victim'
    alt_name = ssxn.Name_of_victim_alternative
    'alternate name of this victim'
    race = ssxn.Race
    'race of the lynching victim'
    date_of_lynching = ssxn.Date_of_lynching
    'date the victim was lynched'
    gender = ssxn.Gender
    'gender of the victim'
    alleged_crime = ssxn.Alleged_crime
    'crime the lynching victim was accused of committing'
    county_of_lynching = ssxn.County
    'county the lynching took place in'
    occupation = ssxn.Occupation
    'occupation of the victim'
    status_in_community = ssxn.Status_in_community
    'status of the victim in the community'

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

    def _all_values(self, *property_names):
        '''Get all values for `property_names` on this object and any
        associated :class:`BrundageVictimData`.
        '''
        items = []
        for property_name in property_names:
            if getattr(self, property_name, None):
                items.append(getattr(self, property_name))
        for property_name in property_names:
            items.extend(getattr(brundage, property_name)
                         for brundage in self.brundage
                         if getattr(brundage, property_name, None))
        return items

    def _primary_value(self, *property_names):
        '''Get the primary value for `property_names` for this victim. Try
        each property names on this object. If this object doesn't have data
        for any of them, then try each of the associated Brundage data
        objects in turn. Ordering of Brundage data is not guaranteed, though
        property order for each is maintained.
        '''
        for property_name in property_names:
            if getattr(self, property_name, None):
                return getattr(self, property_name)
        brundage_values = []
        for brundage in self.brundage:
            for property_name in property_names:
                if getattr(brundage, property_name, None):
                    brundage_values.append(getattr(brundage, property_name))
        if brundage_values:
            if len(brundage_values) > 1:
                logger.info('%s: multiple Brundage values for victim %s. picking arbitrarily' %
                    (property_name, self.id))
            return brundage_values[0]
        logger.info('%s: no value for victim %s' % (property_name, self.id))

    @property
    def all_names(self):
        return self._all_values('name', 'alt_name')
    @property
    def primary_name(self):
        return self._primary_value('name', 'alt_name')

    @property
    def all_counties(self):
        return self._all_values('county_of_lynching')
    @property
    def primary_county(self):
        return self._primary_value('county_of_lynching')

    @property
    def all_alleged_crimes(self):
        return self._all_values('alleged_crime')
    @property
    def primary_alleged_crime(self):
        return self._primary_value('alleged_crime')

    @property
    def all_lynching_dates(self):
        return self._all_values('date_of_lynching')
    @property
    def primary_lynching_date(self):
        return self._primary_value('date_of_lynching')


class BrundageVictimData(ComplexObject):
    '''A BrundageVictimData is supplementary data about a victim collected
    from an external source named Brundage.
    '''

    rdf_type = scxn.Victim_Brundage
    'the URI of the RDF Class describing victim Brundage data'

    name = ssxn.Name_of_victim_Brundage
    'name of this victim'
    county_of_lynching = ssxn.County_of_lynching_Brundage
    'county the lynching took place in'
    alleged_crime = ssxn.Alleged_crime_Brundage
    'crime the lynching victim was accused of committing'
    date_of_lynching = ssxn.Date_of_lynching_Brundage
    'date the victim was lynched'
    mob_type = ssxn.Mob_type_Brundage
    'short textual description of the type of mob that performed the lynching'
    race = ssxn.Race_Brundage
    'race of the lynching victim'

    victim = ReversedRdfPropertyField(sxcxcxn.Victim_Brundage,
                                      result_type=Victim,
                                      reverse_field_name='brundage')
