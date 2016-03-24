#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    dirq.py

    Directory Query, command-line interface

"""

from __future__ import print_function
from __future__ import unicode_literals
import logging
import argparse
import json
try:
    import configparser
except ImportError:
    # Fall back to Python2 module name
    import ConfigParser as configparser
import ldap3

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
    if isinstance(raw_value, list):
        return " ".join(raw_value)
    else:
        return str(raw_value)


# When called directly as a script...
if __name__ == '__main__':
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
    args = parser.parse_args()
    print(args)

    # Setup logging system
    logging.basicConfig(level=args.loglevel,
                        format='%(levelname)-8s %(message)s')

    # Load configuration
    config = load_configuration(args.config_file)

    # During development, add logging from ldap3 library to our log stream
    #ldap3.utils.log.set_library_log_detail_level(ldap3.utils.log.BASIC)

    formatters = {"title":format_multivalue_string}

    # Establish the set of servers we will contact
    # Iteratively build the server list to work around ldap3 not
    # accepting formatter in ServerPool calls
    logging.debug("Attempting connections to %s", config["server"]["uris"])
    server_list = []
    for uri in config["server"]["uris"]:
        this_server = ldap3.Server(uri, formatter=formatters)
        server_list.append(this_server)

    server_pool = ldap3.ServerPool(server_list, pool_strategy=ldap3.FIRST, active=True)

    # Define the set of all attributes we will query
    server_attributes = [ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES]
    if config["server"]["add_attributes"]:
        server_attributes.extend(config["server"]["add_attributes"])

    # TODO: Consider schema load/save
    # TODO: Add user options, SSL/TLS options to connection
    with ldap3.Connection(server_pool, read_only=True) as conn:
        #conn.search(config["server"]["base"], config["search"]["filter"])
        #for entry in conn.response
        logging.debug("Reached server %s", conn.server)
        entry_generator = conn.extend.standard.paged_search(search_base=config["server"]["base"],
                                                            search_filter=config["searches"]["default"],
                                                            search_scope=ldap3.SUBTREE,
                                                            attributes=server_attributes,
                                                            get_operational_attributes=True,
                                                            paged_size=10,
                                                            generator=True)
        # Keep a counter, so the non-dict object from conn.entries can be accessed
        # Other approach iterates entry in conn.response to access a dict version
        entry_counter = 0
        for entry in entry_generator:
            logging.debug(len(conn.entries))
            logging.info(entry)
            logging.info(conn.entries[entry_counter].entry_to_ldif())
            output_string = str(config["outputs"]["default"]).format(dn=entry["dn"], **entry["attributes"])
            print(output_string)
            entry_counter += 1
