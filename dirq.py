#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    dirq.py

    Directory Query, command-line interface

"""

from __future__ import print_function
from __future__ import unicode_literals
import logging
import string
import argparse
import json
try:
    import configparser
except ImportError:
    # Fall back to Python2 module name
    import ConfigParser as configparser
import sys

# Non-standard imports
import ldap3

# Package imports
import DirectoryQuery.utils
import DirectoryQuery.config

# Pseudo-code
#   Establish directory instance(s)
#     Initiate connections to directories
#     Load custom search terms/attributes (tailor directories)
#   Conduct search across each directory
#     Auto-match search terms with known attributes
#     Run the search against the directory attributes
#   Present results
#   Cleanup directory instance(s)
#     Teardown any outstanding connections


def load_configuration(configuration_source, parent_configuration={}):
    assert configuration_source is not None
    config = parent_configuration
    with open(configuration_source) as json_config_file:
        config = json.load(json_config_file)
    return config


def format_multivalue_string(raw_value):
    logging.info(">>>>>>>>>>>>>>> format_multivalue_string={}".format(raw_value))
    if isinstance(raw_value, list):
        return u' '.join(raw_value)
    else:
        return str(raw_value)


def main(argv):
    # Setup the command line arguments.
    parser = argparse.ArgumentParser(description='Query a central directory')
    parser.add_argument('-q', '--quiet', help='minimize logging output',
                        dest='loglevel', action='store_const',
                        const=logging.ERROR, default=logging.INFO)
    parser.add_argument('-d', '--debug', help='maximize logging output',
                        dest='loglevel', action='store_const',
                        const=logging.DEBUG, default=logging.INFO)
    parser.add_argument('-v', '--verbose', help='verbose logging output',
                        dest='loglevel', action='store_const',
                        const=logging.INFO, default=logging.INFO)
    parser.add_argument('--config', help='specify a configuration file',
                        dest='config_file', default="config.json")
    args = parser.parse_args(argv)
    print(args)

    # Setup logging system
    logging.basicConfig(level=args.loglevel,
                        format='%(levelname)-8s %(message)s')

    # Load configuration, validate parts
    config = load_configuration(args.config_file)

    # Test config
    myconfig = DirectoryQuery.config.Config(filename=args.config_file)
    myoutput = myconfig.service()
    logging.info("==*== services\n         {:s}".format(myconfig.services))
    logging.info("==*== servers[0]\n         {:s}".format(myoutput.servers[0]))
    logging.info("==*== outputs[_simple]\n         {:s}".format(myoutput.outputs["_simple"]))
    logging.info("==*== outputs[default]\n         {:s}".format(myoutput.outputs["default"]))
    logging.info("==*== searches[default]\n         {:s}".format(myoutput.searches["default"]))
    logging.info("==*==")


    # During development, add logging from ldap3 library to our log stream
    #ldap3.utils.log.set_library_log_detail_level(ldap3.utils.log.BASIC)

    formatters = {u'title': format_multivalue_string}

    # Define the set of all attributes we will query, assemble from the
    # service/server configuration, and fields used by the selected output.
    attributes_to_query = myoutput.servers[0].attributes
    attributes_to_query |= myoutput.outputs["default"].named_format_elements
    # Remove dn to avoid a duplicate key error in output, where we auto-force
    # dn inclusion anyway in the record display loop
    attributes_to_query.discard("dn")
    logging.debug("attributes_to_query={}".format(attributes_to_query))


    ##########
    # FIXME
    logging.debug("CONFIG=%s", myconfig)
    logging.error("ABORTING AT DEVELOPER INSISTENCE FOR TESTING")
    return 1
    ##########

    # Establish the set of servers we will contact
    # Iteratively build the server list to work around ldap3 not
    # accepting formatter in ServerPool calls
    logging.debug("Attempting connections to %s", config["service"]["server"]["uris"])
    server_list = []
    for uri in config["service"]["server"]["uris"]:
        this_server = ldap3.Server(uri, formatter=formatters)
        server_list.append(this_server)
    server_pool = ldap3.ServerPool(server_list, pool_strategy=ldap3.FIRST, active=True)

    # TODO: Consider schema load/save
    # TODO: Add user options, SSL/TLS options to connection
    with ldap3.Connection(server_pool, read_only=True, return_empty_attributes=True) as conn:
        #conn.search(config["service"]["server"]["base"], config["search"]["filter"])
        #for entry in conn.response
        logging.debug("Reached server %s", conn.server)
        attribute_list = list(attributes_to_query)
        entry_generator = conn.extend.standard.paged_search(search_base=config["service"]["server"]["base"],
                                                            search_filter=config["service"]["searches"]["default"],
                                                            search_scope=ldap3.SUBTREE,
                                                            attributes=attribute_list,
                                                            get_operational_attributes=True,
                                                            paged_size=10,
                                                            generator=True)
        # Keep a counter, so the non-dict object from conn.entries can be accessed
        # Other approach iterates entry in conn.response to access a dict version
        entry_counter = 0
        for entry in entry_generator:
            logging.info("Current entry ({} of {}): ==>\n{}\n<===".format(entry_counter, conn.entries, entry))
            logging.info("LDIFoutput: ==>\n{}\n<===".format(conn.entries[entry_counter].entry_to_ldif()))
            # TODO: convert the multi-value attributes presented as lists to output-compatible formats like strings
            output_string = str(config["service"]["outputs"]["default"]).format(dn=entry["dn"], **entry["attributes"])
            print(output_string)
            entry_counter += 1

# When called directly as a script...
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
