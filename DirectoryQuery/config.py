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
        self.attributes = set([u'objectClass'])

        for uri in args:
            self.uris.append(uri)
        for uri in kwargs["uris"]:
            self.uris.append(uri)
        if kwargs["base"]:
            self.base = kwargs["base"]
        for attribute in kwargs["add_attributes"]:
            self.attributes.add(attribute)

    def __repr__(self):
        return(u'{}.{}(uris={}, base=\"{}\", attributes={})'
               u''.format(self.__module__,
                          type(self).__name__,
                          self.uris,
                          self.base,
                          self.attributes))


class Search(object):
    """ Class for a search setup """
    def __init__(self, *args, **kwargs):
        logging.debug("Search: {}".format(kwargs))
        self.filter = None

        for filter_string in args:
            self.filter = filter_string
        self.filter = kwargs.setdefault(u'filter', None)

    def __repr__(self):
        return (u'{}.{}({})'
                u''.format(self.__module__,
                           type(self).__name__,
                           self.filter))


class Output(object):
    """ Class for output formats """
    def __init__(self, *args, **kwargs):
        logging.debug("Output: {}".format(kwargs))
        self.output = None
        self.all_format_elements = None
        self.named_format_elements = None

        for output_string in args:
            self.output = output_string
        self.output = kwargs.setdefault(u'output', None)

        if self.output:
            self.all_format_elements = DirectoryQuery.utils.get_format_fields(self.output)
            self.named_format_elements = DirectoryQuery.utils.get_named_format_fields(self.output)
            #if self.all_format_elements != self.named_format_elements:
            #    logging.warn("Output type \"%s\" uses un-named fields, un-expected output may result.", name)

    def __repr__(self):
        return (u'{}.{}({})'
                u''.format(self.__module__,
                           type(self).__name__,
                           self.output))


class Service(object):
    """
    A Service is an encapsulation of the specific information required
    to access a particular directory service instantiation. This includes
    the URI(s) to contact, one or more searches that can be run against
    any of those URIs, and one or more registry the end-user can use to
    format the output from the search.

    """
    def __init__(self, *args, **kwargs):
        self.servers = []
        self.searches = dict()
        self.outputs = dict()
        self.default_output = None
        self.default_search = None

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
        for name, filter_string in search.items():
            logging.debug("Adding search configuration {}".format(search))
            self.searches[name] = Search(filter=filter_string)
        if not self.default_search:
            self.default_search = name

    def add_output(self, output=dict()):
        for name, output_string in output.items():
            logging.debug("Adding output configuration {}".format(output))
            self.outputs[name] = Output(output=output_string)
            if not self.default_output:
                self.default_output = name
            if self.outputs[name].all_format_elements != self.outputs[name].named_format_elements:
                logging.warn("Output type \"%s\" uses un-named fields, un-expected output may result.", name)


    def __repr__(self):
        args = []
        args.append(u'server=["{}"]'
                    u''.format(self.servers))
        args.append(u'searches=["{}"]'
                    u''.format(self.searches))
        args.append(u'outputs=["{}"]'
                    u''.format(self.outputs))

        return (u'{}.{}({})'
                u''.format(self.__module__,
                           type(self).__name__,
                           u', '.join(args)))


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
        return(self.services_available.keys())

    def service(self, name=None):
        svc = None
        if not name:
            name = self.default_service
        if name in self.services_available:
            svc = self.services_available[name]
        return svc

    def __repr__(self):
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
