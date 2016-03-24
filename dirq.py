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
