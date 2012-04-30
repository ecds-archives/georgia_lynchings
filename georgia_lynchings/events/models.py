import logging
from datetime import datetime

from django.db.models import permalink

from georgia_lynchings.rdf.fields import RdfPropertyField, \
    ReversedRdfPropertyField, ChainedRdfPropertyField, UnionRdfPropertyField
from georgia_lynchings.rdf.models import ComplexObject
from georgia_lynchings.rdf.ns import scxn, ssxn, sxcxcxn, ix_mbd, dcx

logger = logging.getLogger(__name__)

class MacroEvent(ComplexObject):
    '''A Macro Event is an object type defined by the project's (currently
    private) PC-ACE database. It represents a lynching case and all of the
    individual events associated with it.
    '''

    rdf_type = scxn.Macro_Event
    'the URI of the RDF Class describing macro event objects'     

    @permalink
    def get_absolute_url(self):
        return ('events:detail', [str(self.id)])

    # NOTE: Fields for complex subobjects are defined on the subobjects
    # themselves to simplify syntax. For example, see Event.macro_event,
    # below, which adds an "events" property to MacroEvent with its
    # reverse_field_name.


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
        if self.brundage: # TODO check if this is proper bug fix when brundage is none.
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
        if not self._primary_value('date_of_lynching'):
            return None
        date = datetime.strptime(self._primary_value('date_of_lynching'), "%Y-%m-%d").date()
        return date


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
