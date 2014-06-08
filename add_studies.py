#!/usr/bin/env/python
"""
    add-studies.py -- From a data file consisting of human subject studies
    add or update sydies in VIVO

    Version 0.0 MC 2014-06-06
    --  just starting
"""

__author__ = "Michael Conlon"
__copyright__ = "Copyright 2014, University of Florida"
__license__ = "BSD 3-Clause license"
__version__ = "0.0"

__harvest_text__ = "Python Studies " + __version__

from vivotools import vivo_sparql_query
from vivotools import get_vivo_uri
from vivotools import assert_resource_property
from vivotools import assert_data_property
from vivotools import update_data_property
from vivotools import update_resource_property
from vivotools import rdf_header
from vivotools import rdf_footer
from vivotools import find_vivo_uri
from vivotools import untag_predicate
from vivotools import get_triples

from datetime import datetime
import json

def get_study(study_uri):
    """
    Given the URI of a study, return an object that contains the
    study it represents.
    """
    study = {}
    study['uri'] = study_uri
    study['concept_uris'] = []
    study['authorship_uris'] = []
    triples = get_triples(study_uri)
    try:
        count = len(triples["results"]["bindings"])
    except:
        count = 0
    i = 0
    while i < count:
        b = triples["results"]["bindings"][i]
        p = b['p']['value']
        o = b['o']['value']
        if p == "http://www.w3.org/2000/01/rdf-schema#label":
            study['title'] = o
        if p == "http://vivoweb.org/ontology/core#description":
            study['description'] = o
        if p == "http://vivo.ufl.edu/ontology/vivo-ufl/irbnumber":
            study['irb_number'] = o
        if p == "http://vivoweb.org/ontology/core#hasSubjectArea":
            study['concept_uris'].append(o)
        if p == \
           "http://vivoweb.org/ontology/core#informationResourceInAuthorship":
            study['authorship_uris'].append(o)
        i = i + 1
    return study

def update_study(vivo_study, source_study)
    """
    given a vivo study and a source data study, create a key table to provide
    attributes to be updated and instions on how to update them.  Given the
    objects and instructions to update_entity to do the work
    """
    key_table = {
        'concept_uris': {'predicate': 'vivo:hasSubjectArea',
                        'action': 'resource_list'}
        'authorship_uris': {'predicate': 'vivo:informationResourceInAuthorship',
                        'action': 'resource_list'}
        'title':{'predicate': 'rdfs:label',
                        'action': 'literal'}
        'irb_number':{'predicate': 'ufVivo:irbnumber',
                        'action': 'literal'}
        'description':{'predicate': 'vivo:description',
                        'action': 'literal'}
        }
    return update_entity(vivo_study, source_study, key_table)

def update_entity(vivo_entity, source_entity, key_table):
    """
    Given a VIVO entity and a source entity, go through the elements
    in the key_table and update VIVO as needed
    """
    entity_uri = vivo_entity['uri']
    ardf = ""
    srdf = ""
    for key in key_table.keys():
        action = key_table['key']['action']
        if action == 'literal':
            if key in vivo_entity:
                vivo_value = vivo_entity[key]
            else:
                vivo_value = None
            if key in source_entity:
                source_value = source_entity[key]
            else:
                source_value = None
            [add, sub] = update_data_property(entity_uri,
                key_table[key]['predicate'], vivo_value, source_value)
            ardf = ardf + add
            srdf = srdf + sub
        elif action == 'resource':
            if key in vivo_entity:
                vivo_value = vivo_entity[key]
            else:
                vivo_value = None
            if key in source_entity:
                source_value = source_entity[key]
            else:
                source_value = None
            [add, sub] = update_resource_property(entity_uri,
                key_table[key]['predicate'], vivo_value, source_value)
            ardf = ardf + add
            srdf = srdf + sub
        elif action = 'literal_list':
            vals = vivo_entity[key]+source_entity[key]
            for val in vals:
                if val in vivo_entity and val in source_entity:
                    pass
                elif val in vivo_entity and val not in source_entity:
                    [add, sub] = update_data_property(entity_uri,
                        key_table[key]['predicate'], val, None)
                    ardf = ardf + add
                    srdf = srdf + sub
                else:
                    [add, sub] = update_data_property(entity_uri,
                        key_table[key]['predicate'], None, val)
                    ardf = ardf + add
                    srdf = srdf + sub
        elif action = 'resource_list':
            vals = vivo_entity[key]+source_entity[key]
            for val in vals:
                if val in vivo_entity and val in source_entity:
                    pass
                elif val in vivo_entity and val not in source_entity:
                    [add, sub] = update_resource_property(entity_uri,
                        key_table[key]['predicate'], val, None)
                    ardf = ardf + add
                    srdf = srdf + sub
                else:
                    [add, sub] = update_resource_property(entity_uri,
                        key_table[key]['predicate'], None, val)
                    ardf = ardf + add
                    srdf = srdf + sub
        else:
            raise ActionError(action)
    return [ardf, srdf]

def add_study()
    """
    create a study entity
    """
    return add_entity('ero:ERO_0000015')

def add_entity(tag):
    """
    given a tag, create an entity of that type
    """
    ardf = ""
    uri = get_vivo_uri()
    add = assert_resource_property(uri, "rdf:type",
                                   untag_predicate('owl:Thing'))
    ardf = ardf + add
    add = assert_resource_property(uri, "rdf:type", untag_predicate(tag))
    ardf = ardf + add
    return [ardf, uri]

def prepare_studies(raw_studies):
    """
    Given study data, prepare the data for use in the VIVO update functions.
    This involves naming things using VIVO Tools conventions, replacing
    author UFID with author_uri in VIVO, and replacing keyword text with
    concept_uris in VIVO
    """
    studies = []
    for study in raw_studies:
        study['irb_number'] = study['Irb_number']
        study['title'] = study['project_title']
        study['description'] = study['study_description']
        study['concept_uris'] = []
        inv_uri = find_vivo_uri('ufVivo:ufid', study['UFID'])
        if inv_uri is not None:
            print "Found investigator", study['UFID'], "at", inv_uri
            # Uh, more work here.  You need to try to find the authorship
            # before you try to make one
            [add, authorship_uri] = make_authorship_rdf()
            study['authorship_uris'] = [authorship_uri]
            ardf = ardf + add
        else:
            print "Not found", study['UFID']
        for key in ['keyword1', 'keyword2', 'keyword3', 'keyword4', 'keyword5']:
            concept_name = study[key]
            if concept_name = '' or concept_name = 'sa':
                continue
            if concept_name in concept_dictionary:
                study['concept_uris'].append(concept_dictionary[concept_name])
            else:
                [add, concept_uri] = make_concept_rdf(keyword_name)
                ardf = ardf + add
                concept_dictionary[concept_name] = concept_uri
                study['concept_uris'].append(concept_uri)
    studies.append(study)
    return [ardf, studies]

# Start here

print datetime.now(), "Start"
print datetime.now(), "Read Study Data"
studies_file = open("studies_2014-06-06_3 pm.json", "r")
studies = prepare_studies(json.load(studies_file))
studies_file.close()
print datetime.now(), "Study Data has", len(studies), "studies"
ardf = rdf_header()
srdf = rdf_header()

# Main loop

for study in studies:
    study_uri = find_vivo_uri('ufVivo:IRBNumber', study['Irb_number'])
    if study_uri is not None:
        print "Updating Study at",study_uri
        [add, sub] = update_study(vivo_study, study)
        ardf = ardf + add
        srdf = srdf + sub
    else:
        print "Adding Study"
        [add, study_uri] = add_study()
        vivo_study = {'uri': study_uri}
        ardf = ardf + add
        [add, sub] = update_study(vivo_study, study)

adrf = ardf + rdf_footer()
srdf = srdf + rdf_footer()
add_file = open("studies_add.rdf", "w")
sub_file = open("studies_sub.rdf", "w")
print >>add_file, adrf
print >>sub_file, srdf
add_file.close()
sub_file.close()
print datetime.now(), "Finished"
