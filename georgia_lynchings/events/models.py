from django.db import models
from georgia_lynchings.events.rdfns import dcx, scx, ssx, sxcxcx

class MacroEvent(object):
    '''A Macro Event is an object type defined by the project's (currently
    private) PC-ACE database. It represents a lynching case and all of the
    individual events associated with it.
    '''
    # NOTE: Many of these relationships are defined in the private PC-ACE
    # database for this project. The URIs were found a priori by examining
    # the RDF data imported from the database setup tables.

    rdf_type = scx.r1
    'the URI of the RDF Class describing macro event objects'

    # Every PC-ACE complex object has a label. TODO: Consider extracting a
    # parent class to reflect this?
    label = dcx.Identifier
    'a human-readable label for this macro event'

    # complex fields potentially attached to a MacroEvent
    events = sxcxcx.r61
    'the events associated with this macro event'

    # simplex fields potentially attached to a MacroEvent
    county = ssx.r18
    'the county in which the lynching occurred'
    victim = ssx.r82
    'the victim of the lynching'
    case_number = ssx.r84
    'a case number identifying this lynching case'
    verified_semantic = ssx.r89
    '''has the coded data for this case been manually reviewed for semantic
    consistency?'''
    verified_details = ssx.r90
    '''has the coded data for this case been manually reviewed for detail
    accuracy?'''
    last_coded = ssx.r94
    'the date this case most recently had coding data added'
