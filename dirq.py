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

def load_configuration(configuration_source, parent_configuration=None):
    assert configuration_source is not None
    config = parent_configuration or dict()
    with open(configuration_source) as json_config_file:
        config = json.load(json_config_file)
    return config

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

    # Load configuration
    myconfig = DirectoryQuery.config.Config(filename=args.config_file)
    myservice = myconfig.service()
    myserver = myservice.servers[0]
    mysearch = myservice.searches["default"]
    myoutputs = myservice.outputs
    myoutput = myservice.outputs["default"]
    logging.info("==*== services\n         %s", myconfig.services)
    logging.info("==*== servers[0]\n         %s", myserver)
    logging.info("==*== outputs[_simple]\n         %s", myoutputs["_simple"])
    logging.info("==*== outputs[default]\n         %s", myoutput)
    logging.info("==*== searches[default]\n         %s", mysearch)
    logging.info("==*==")

    # During development, add logging from ldap3 library to our log stream
    #ldap3.utils.log.set_library_log_detail_level(ldap3.utils.log.BASIC)

    ##########
    # FIXME
    logging.debug("CONFIG=%s", myconfig)
    logging.error("ABORTING AT DEVELOPER INSISTENCE FOR TESTING")
    #return 1
    ##########

    # Connect to the specified Service's Server
    logging.debug("Attempting connections to %s", myserver.uris)
    record_count = 0
    for record in myservice.query():
        if record_count:
            print()
        print(record)
        record_count += 1
    else:
        print()
        logging.info("Total of %d records", record_count)

# When called directly as a script...
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
