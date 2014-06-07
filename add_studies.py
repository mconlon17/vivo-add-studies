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

from datetime import datetime
import json

def update_study(study_uri, study):
    """
    Given the uri of a study in VIVO and study data,
    generate add and sub RDF to update the study in VIVO
    with the data in study
    """
    ardf = ""
    srdf = ""
    return [ardf, srdf]

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

# Start here

print datetime.now(), "Start"
print datetime.now(), "Read Study Data"
studies_file = open("studies_2014-06-06_3 pm.json", "r")
studies = json.load(studies_file)
studies_file.close()
print datetime.now(), "Study Data has", len(studies)
ardf = rdf_header()
srdf = rdf_header()

# Main loop

for study in studies:
    inv_uri = find_vivo_uri('ufVivo:ufid', study['UFID'])
    if inv_uri is not None:
        print "Found investigator", study['UFID'],"at", inv_uri
    else:
        print "Not found", study['UFID']
        continue

    study_uri = find_vivo_uri('ufVivo:IRBNumber', study['Irb_number'])
    if study_uri is not None:
        print "Updating Study at",study_uri
        [add, sub] = update_study(study_uri, study)
        ardf = ardf + add
        srdf = srdf + sub
    else:
        print "Adding Study"
        [add, study_uri] = add_entity('ero:ERO_0000015')
        ardf = ardf + add
        [add, sub] = update_study(study_uri, study)

adrf = ardf + rdf_footer()
srdf = srdf + rdf_footer()
add_file = open("studies_add.rdf", "w")
sub_file = open("studies_sub.rdf", "w")
print >>add_file, adrf
print >>sub_file, srdf
add_file.close()
sub_file.close()
print datetime.now(), "Finished"
