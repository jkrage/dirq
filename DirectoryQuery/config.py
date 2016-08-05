#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    config.py

    DirectoryQuery, configuration support

"""
import logging
import json
import codecs

# Package imports
import DirectoryQuery.utils


class Server(object):
    """ Class for server information """
    def __init__(self, *args, **kwargs):
        self.uris = []
        self.base = None
        self.attributes = set(["objectClass"])

        for uri in args:
            self.uris.append(uri)
        for uri in kwargs["uris"]:
            self.uris.append(uri)
        if kwargs["base"]:
            self.base = kwargs["base"]
        for attribute in kwargs["add_attributes"]:
            self.attributes.add(attribute)

    def __repr__(self):
        return("{}.{}(uris={}, base=\"{}\", attributes={})"
               "".format(self.__module__,
                         type(self).__name__,
                         self.uris,
                         self.base,
                         self.attributes))


class Searches(object):
    """ Class for search information """
    def __init__(self, *args, **kwargs):
        logging.debug("Searches: {}".format(kwargs))
        self.filters = dict()

        for name, search in kwargs.items():
            self.filters[name] = search

    def filter(self, filter_name):
        filter = None
        if filter_name in self.filters:
            filter = self.filters[filter_name]
        return filter

    def __repr__(self):
        return("{}.{}({})"
               "".format(self.__module__,
                         type(self).__name__,
                         self.filters))


class Outputs(object):
    """ Class for output formats """
    def __init__(self, *args, **kwargs):
        logging.debug("Outputs: {}".format(kwargs))
        self.formats = dict()

        for name, output_string in kwargs.items():
            self.formats[name] = output_string

            # TODO: Consider keeping copies of these sets in an Output class
            all_format_elements = DirectoryQuery.utils.get_format_fields(output_string)
            named_format_elements = DirectoryQuery.utils.get_named_format_fields(output_string)
            if all_format_elements != named_format_elements:
                logging.warn("Output type \"%s\" uses un-named fields, un-expected output may result.", name)

    def __repr__(self):
        return ("{}.{}({})"
                "".format(self.__module__,
                          type(self).__name__,
                          self.formats))


class Service(object):
    """
    A Service is an encapsulation of the specific information required
    to access a particular directory service instantiation. This includes
    the URI(s) to contact, one or more searches that can be run against
    any of those URIs, and one or more outputs the end-user can use to
    format the output from the search.

    """
    def __init__(self, *args, **kwargs):
        self.servers = []
        self.searches = []
        self.outputs = []

        self.section_map = {'server': self.add_server,
                            'searches': self.add_search,
                            'outputs': self.add_output
                            }

        # Extract known sections from incoming settings
        for section in self.section_map:
            logging.debug("Seeking config section {}".format(section))
            if section in kwargs:
                self.section_map[section](kwargs[section])
        logging.debug("Config.servers  = {}".format(self.servers))
        logging.debug("Config.searches = {}".format(self.searches))
        logging.debug("Config.outputs  = {}".format(self.outputs))

    def add_server(self, server=dict()):
        logging.debug("Adding server configuration {}".format(server))
        self.servers.append(Server(**server))

    def add_search(self, search=dict()):
        logging.debug("Adding search configuration {}".format(search))
        self.searches.append(Searches(**search))

    def add_output(self, output=dict()):
        logging.debug("Adding output configuration {}".format(output))
        self.outputs.append(Outputs(**output))


class Config(object):
    def __init__(self, *args, **kwargs):
        self.services_available = dict()
        self.encoding = "utf-8"
        self.default_service = None

        if "filename" in kwargs:
            logging.debug("Config.filename={}".format(kwargs["filename"]))
            self._filename = kwargs["filename"]
            self._config = self.load_configuration(kwargs["filename"], encoding=self.encoding)
        logging.debug("_config={}".format(self._config))

        # TODO: accept additional configs in kwargs
        for svc in self._config:
            service = self._config[svc]
            self.services_available[service["name"]] = Service(name=service["name"],
                                                               server=service["server"],
                                                               searches=service["searches"],
                                                               outputs=service["outputs"])
            if not self.default_service or service["name"].is_default:
                self.default_service = service["name"]

    @property
    def services(self):
        return(frozenset(self.services_available.keys()))

    def service(self, name=None):
        svc = None
        if not name:
            name = self.default_service
        if name in self.services_available:
            svc = self.services_available[name]
        return svc

    def __str__(self):
        args = []
        if self._filename:
            args.append(u'filename="{}"'.format(self._filename))

        args.append(u'services=["{}"]'
                    u''.format(u'","'.join(self.services_available.keys())))

        return(u'{}.{}({})'
               u''.format(self.__module__,
                          type(self).__name__,
                          u', '.join(args)))

    @staticmethod
    def load_configuration(configuration_source, parent_configuration=None, encoding="utf-8"):
        """

        :type configuration_source: string
        :type parent_configuration: dict
        """
        assert configuration_source is not None
        if parent_configuration:
            config = parent_configuration
        with codecs.open(configuration_source, "rt", encoding=encoding) as json_config_file:
            config = json.load(json_config_file)
        return config
