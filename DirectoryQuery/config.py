#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    config.py

    DirectoryQuery, configuration support

"""
from __future__ import unicode_literals
import logging
import string
import json
import ldap3


class Server(object):
    """ Class for server information """
    def __init__(self, *args, **kwargs):
        logging.debug("Server: {}".format(kwargs))
        self.uris = None
        self.base = None
        self.add_attributes = None


class Searches(object):
    """ Class for search information """
    def __init__(self, *args, **kwargs):
        logging.debug("Searches: {}".format(kwargs))
        self.label = None


class Outputs(object):
    """ Class for output formats """
    def __init__(self, *args, **kwargs):
        logging.debug("Outputs: {}".format(kwargs))
        self.label = None


class Config(object):
    def __init__(self, *args, **kwargs):
        self.servers = set()
        self.searches = set()
        self.outputs = set()

        self.section_map = {'server': self.add_server,
                            'searches': self.add_search,
                            'outputs': self.add_output
                            }

        if "filename" in kwargs:
            logging.debug("Config.filename={}".format(kwargs["filename"]))
            self._config = self.load_configuration(kwargs["filename"])
        logging.debug("_config={}".format(self._config))

        # Extract known sections from incoming settings
        for section in self.section_map:
            logging.debug("Seeking config section {}".format(section))
            if section in self._config:
                self.section_map[section](self._config[section])
            if section in kwargs:
                self.section_map[section](kwargs[section])
        logging.debug("Config.servers  = {}".format(self.servers))
        logging.debug("Config.searches = {}".format(self.searches))
        logging.debug("Config.outputs  = {}".format(self.outputs))

    def add_server(self, server={}):
        logging.debug("Adding server configuration {}".format(server))
        self.servers.add(Server(**server))

    def add_search(self, search={}):
        logging.debug("Adding search configuration {}".format(search))
        self.searches.add(Searches(**search))

    def add_output(self, output={}):
        logging.debug("Adding output configuration {}".format(output))
        self.outputs.add(Outputs(**output))

    @staticmethod
    def load_configuration(configuration_source, parent_configuration={}):
        """

        :type configuration_source: string
        :type parent_configuration: dict
        """
        assert configuration_source is not None
        config = parent_configuration
        with open(configuration_source, "rt") as json_config_file:
            config = json.load(json_config_file)
        return config
