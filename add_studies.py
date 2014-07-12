#!/usr/bin/env/python
"""
    add-studies.py -- From a data file consisting of human subject studies
    add or update sydies in VIVO

    Version 0.0 MC 2014-06-06
    --  just starting
    Version 0.1 MC 2014-06-11
    --  file name from command line.  Convert unicode to XML char on output.
        All attributes of a study are optional except for IRBnumber.
    Version 0.2 MC 2014-07-12
    --  Nearly complete first version

    To Do
    --  Handle authorships
    --  Debug resource list merging
"""

__author__ = "Michael Conlon"
__copyright__ = "Copyright 2014, University of Florida"
__license__ = "BSD 3-Clause license"
__version__ = "0.1"

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
from vivotools import get_vivo_value
from vivotools import untag_predicate
from vivotools import get_triples
from vivotools import get_authorship
from vivotools import make_concept_dictionary
from vivotools import make_concept_rdf
import vivotools as vt

from datetime import datetime
import json
import sys
import os
import codecs

class ActionError(Exception):
    """
    Thrown when an invalid action is found in the key_table for an entity
    update
    """
    pass

def get_study(study_uri):
    """
    Given the URI of a study, return an object that contains the
    study it represents.  Always disambiguate authors
    """
    study = {}
    study['uri'] = study_uri
    study['concept_uris'] = []
    study['authorship_uris'] = []
    study['author_uris'] = []
    study['authors'] = {}
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
            authorship = get_authorship(o)
            if 'author_uri' in authorship:

                #   Add key value which is rank.  Then string_from_document
                #   should show in rank order.  Voila!
                
                author_uri = authorship['author_uri']
                if 'author_rank' in authorship:
                    rank = authorship['author_rank']
                    study['authors'][rank] = {'first':get_vivo_value(author_uri,
                        "foaf:firstName"), 'middle':get_vivo_value(author_uri,
                        "vivo:middleName"), 'last':get_vivo_value(author_uri,
                        "foaf:lastName")}
                study['author_uris'].append(author_uri)
        i = i + 1
    return study

def update_study(vivo_study, source_study):
    """
    given a vivo study and a source data study, create a key table to provide
    attributes to be updated and instructions on how to update them.  Given the
    objects and instructions to update_entity to do the work.
    """
    key_table = {
        'concept_uris': {'predicate': 'vivo:hasSubjectArea',
                        'action': 'resource_list'},
        'authorship_uris': {'predicate': 'vivo:informationResourceInAuthorship',
                        'action': 'resource_list'},
        'title':{'predicate': 'rdfs:label',
                        'action': 'literal'},
        'irb_number':{'predicate': 'ufVivo:irbnumber',
                        'action': 'literal'},
        'description':{'predicate': 'vivo:description',
                        'action': 'literal'},
        'date_harvested':{'predicate': 'ufVivo:dateHarvested',
                        'action': 'literal'},
        'harvested_by':{'predicate': 'ufVivo:harvestedBy',
                        'action': 'literal'}
        }

    # authorships for source study

    
    return update_entity(vivo_study, source_study, key_table)

def update_entity(vivo_entity, source_entity, key_table):
    """
    Given a VIVO entity and a source entity, go through the elements
    in the key_table and update VIVO as needed.

    Four actions are supported:

    literal -- single valued literal.  Such as an entity label
    resource -- single valued reference to another object.  Such as the
        publisher of a journal
    literal_list -- a list of literal values.  Such as phone numbers for
        a person
    resource_list -- a list of references to other objects.  Such as a
        a list of references to concepts for a paper
    """
    print "VIVO Entity", json.dumps(vivo_entity, indent=4)
    print "Source Entity", json.dumps(source_entity, indent=4)
    print "Key Table", key_table
    entity_uri = vivo_entity['uri']
    ardf = ""
    srdf = ""
    for key in key_table.keys():
        action = key_table[key]['action']
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
        elif action == 'literal_list':
            vals = vivo_entity.get(key,[])+source_entity.get(key,[])
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
        elif action == 'resource_list':
            vals = vivo_entity.get(key,[])+source_entity.get(key,[])
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

def make_authorship_rdf(pub_uri, author_uri, rank, corresponding=False):
    """
    Given data values, create the RDF for an authorship
    """
    ardf = ""
    [add, authorship_uri] = add_entity("vivo:Authorship")
    ardf = ardf + add
    add = assert_resource_property(authorship_uri,
        "vivo:linkedAuthor", author_uri)
    ardf = ardf + add
    add = assert_resource_property(authorship_uri,
        "vivo:linkedInformationResource", pub_uri)
    ardf = ardf + add
    add = assert_data_property(authorship_uri,
        "vivo:authorRank", rank)
    ardf = ardf + add
    add = assert_data_property(authorship_uri,
        "vivo:isCorrespondingAuthor", str(corresponding).lower())
    ardf = ardf + add
    return [ardf, authorship_uri]

def add_study(uri=None, harvested=True):
    """
    create a study entity.  Returns the RDF to create the new entity
    and the URI of the new entity
    """
    return add_entity('ero:ERO_0000015', uri=uri, harvested=harvested)

def add_entity(tag, uri=None, harvested=True):
    """
    given a tag, create an entity of that type. If harvested is True, add
    date harvested and harvested by assertions. If uri is None, assign to a
    new URI, otherwise use the provided uri
    """
    ardf = ""
    if uri is None:
        uri = get_vivo_uri()
    add = assert_resource_property(uri, "rdf:type",
                                   untag_predicate('owl:Thing'))
    ardf = ardf + add
    add = assert_resource_property(uri, "rdf:type", untag_predicate(tag))
    ardf = ardf + add
    if harvested:
        add = assert_data_property(uri, "ufVivo:dateHarvested",
                                   str(datetime.now()))
        ardf = ardf + add
        add = assert_data_property(uri, "ufVivo:harvestedBy",
                                   __harvest_text__)
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
    ardf = ""
    for study in raw_studies:
        study['irb_number'] = study['Irb_number']
        if 'project_title' in study:
            study['title'] = study['project_title']
        if 'study_description' in study:
            study['description'] = study['study_description']
        study['concept_uris'] = []
        study['date_harvested'] = str(datetime.now())
        study['harvested_by'] = __harvest_text__
        if 'UFID' in study:
            ufid = study['UFID']
            inv_uri = find_vivo_uri('ufVivo:ufid', ufid)
            if inv_uri is not None:
                print >>log_file, "Found investigator", ufid, "at", \
                      inv_uri
                study['inv_uri'] = inv_uri
            else:
                print >>log_file, "Not found", ufid
        for key in ['keyword1', 'keyword2', 'keyword3', 'keyword4', 'keyword5']:
            if key in study:
                concept_name = study[key].title()
                if concept_name == '' or concept_name == 'sa':
                    continue
                if concept_name in vt.concept_dictionary:
                    study['concept_uris'].append(vt.concept_dictionary\
                                                 [concept_name])
                else:
                    [add, concept_uri] = make_concept_rdf(concept_name)
                    ardf = ardf + add
                    vt.concept_dictionary[concept_name] = concept_uri
                    study['concept_uris'].append(concept_uri)
        studies.append(study)
    return [ardf, studies]

# Start here

if len(sys.argv) > 1:
    input_file_name = str(sys.argv[1])
else:
    input_file_name = "studies.txt"
file_name, file_extension = os.path.splitext(input_file_name)

add_file = codecs.open(file_name+"_add.rdf", mode='w', encoding='ascii',
                       errors='xmlcharrefreplace')
sub_file = codecs.open(file_name+"_sub.rdf", mode='w', encoding='ascii',
                       errors='xmlcharrefreplace')
log_file = sys.stdout
##log_file = codecs.open(file_name+"_log.txt", mode='w', encoding='ascii',
##                       errors='xmlcharrefreplace')
exc_file = codecs.open(file_name+"_exc.txt", mode='w', encoding='ascii',
                       errors='xmlcharrefreplace')

ardf = rdf_header()
srdf = rdf_header()

print >>log_file, datetime.now(), "Start"
print >>log_file, datetime.now(), "Study Ingest Version", __version__
print >>log_file, datetime.now(), "VIVO Tools Version", vt.__version__
print >>log_file, datetime.now(), "Making concept dictionary"
make_concept_dictionary()
print >>log_file, datetime.now(), "Concept dictionary has", \
        len(vt.concept_dictionary), "entries"
print >>log_file, datetime.now(), "Read Study Data"
studies_file = open(input_file_name, "r")
[add, studies] = prepare_studies(json.load(studies_file))
ardf = ardf + add
studies_file.close()
print >>log_file, datetime.now(), "Study Data has", len(studies), "studies"

# Main loop

for study in studies:
    study_uri = find_vivo_uri('ufVivo:irbnumber', study['Irb_number'])
    if study_uri is not None:
        print >>log_file, "Updating Study at",study_uri
        vivo_study = get_study(study_uri)
        [add, sub] = update_study(vivo_study, study)
        ardf = ardf + add
        srdf = srdf + sub
    else:
        print >>log_file, "Adding Study at", study_uri
        [add, study_uri] = add_study(harvested=False)
        vivo_study = {'uri': study_uri}
        ardf = ardf + add
        [add, sub] = update_study(vivo_study, study)
        ardf = ardf + add
        srdf = srdf + sub

adrf = ardf + rdf_footer()
srdf = srdf + rdf_footer()
print >>add_file, adrf
print >>sub_file, srdf
add_file.close()
sub_file.close()
print >>log_file, datetime.now(), "Finished"
