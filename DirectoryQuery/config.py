#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    config.py

    DirectoryQuery, configuration support

"""
import logging
import json
import codecs

# Non-standard imports
import ldap3

# Package imports
import DirectoryQuery.utils


class Server(object):
    """ Class for server information """
    def __init__(self, *args, **kwargs):
        self.uris = []
        self.base = None
        self.attributes = set([u'objectClass'])
        self.ldap_attribute_formatters = {u'title': DirectoryQuery.utils.format_multivalue_string}

        # Combine any provided URIs into a single list
        for uri in args:
            self.uris.append(uri)
        self.uris.extend(kwargs.get(u'uris', list()))

        # Add requested attributes to the server defaults
        self.attributes |= set(kwargs.get(u'add_attributes', list()))

        self.base = kwargs.get(u'base', None)
        self.ldap_pool_strategy = kwargs.get(u'ldap_pool_strategy', ldap3.FIRST)
        self.ldap_pool_active = kwargs.get(u'ldap_pool_active', True)
        self.ldap_pool_exhaust = kwargs.get(u'ldap_pool_exhaust', True)
        self.ldap_scope = kwargs.get(u'ldap_scope', ldap3.SUBTREE)

    def __repr__(self):
        return(u'{}.{}(uris={}, base=\"{}\", attributes={})'
               u''.format(self.__module__,
                          type(self).__name__,
                          self.uris,
                          self.base,
                          self.attributes))

    def build_connection_pool(self):
        # Iteratively build the server list to work around ldap3 not
        # accepting formatter in ServerPool calls
        server_pool = None
        server_list = []
        for uri in self.uris:
            this_server = ldap3.Server(uri, formatter=self.ldap_attribute_formatters)
            server_list.append(this_server)
        if server_list:
            server_pool = ldap3.ServerPool(server_list,
                                           pool_strategy=self.ldap_pool_strategy,
                                           active=self.ldap_pool_active,
                                           exhaust=self.ldap_pool_exhaust)
        return server_pool

    def connection(self):
        # TODO: Consider schema load/save
        # TODO: Add user options, SSL/TLS options to connection
        return ldap3.Connection(self.build_connection_pool(),
                                read_only=True,
                                return_empty_attributes=True)


class Search(object):
    """ Class for a search setup """
    def __init__(self, *args, **kwargs):
        logging.debug("Search: %s", kwargs)
        self.filter = None

        for filter_string in args:
            self.filter = filter_string
        self.filter = kwargs.get(u'filter', None)

    def __repr__(self):
        return (u'{}.{}({})'
                u''.format(self.__module__,
                           type(self).__name__,
                           self.filter))


class Output(object):
    """ Class for output formats """
    def __init__(self, *args, **kwargs):
        logging.debug("Output: %s", kwargs)
        self.output = None
        self.all_format_elements = None
        self.named_format_elements = None

        for output_string in args:
            self.output = output_string
        self.output = kwargs.get(u'output', None)

        if self.output:
            self.all_format_elements = DirectoryQuery.utils.get_format_fields(self.output)
            self.named_format_elements = DirectoryQuery.utils.get_named_format_fields(self.output)

    def __repr__(self):
        return (u'{}.{}({})'
                u''.format(self.__module__,
                           type(self).__name__,
                           self.output))


class Service(object):
    """ Service is an encapsulation of the specific information required
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

        self.section_map = {u'server': self.add_server,
                            u'searches': self.add_search,
                            u'outputs': self.add_output
                           }

        # Extract known sections from incoming settings
        for section in self.section_map:
            logging.debug("Seeking config section %s", section)
            if section in kwargs:
                self.section_map[section](kwargs[section])
        logging.debug("Config.servers  = %s", self.servers)
        logging.debug("Config.searches = %s", self.searches)
        logging.debug("Config.outputs  = %s", self.outputs)

    def add_server(self, server=None):
        logging.debug("Adding server configuration %s", server)
        self.servers.append(Server(**server))

    def add_search(self, search=None):
        for name, filter_string in search.items():
            logging.debug("Adding search configuration %s", search)
            self.searches[name] = Search(filter=filter_string)
        if not self.default_search:
            self.default_search = name

    def add_output(self, output=None):
        for name, output_string in output.items():
            logging.debug("Adding output configuration %s", output)
            self.outputs[name] = Output(output=output_string)
            if not self.default_output:
                self.default_output = name
            if self.outputs[name].all_format_elements != self.outputs[name].named_format_elements:
                logging.warn("Output type \"%s\" uses un-named fields,"
                             "un-expected output may result.", name)

    def query(self, output_name="default", search_name="default"):
        myserver = self.servers[0]
        myoutput = self.outputs[output_name]
        mysearch = self.searches[search_name]

        # TODO: Move attribute analysis into Search
        # Define the set of all attributes we will query, assemble from the
        # service/server configuration, and fields used by the selected output.
        attributes_to_query = myserver.attributes
        attributes_to_query |= myoutput.named_format_elements
        # Remove dn to avoid a duplicate key error in output, where we auto-force
        # dn inclusion anyway in the record display loop
        attributes_to_query.discard("dn")
        logging.debug("attributes_to_query=%s", attributes_to_query)

        found_records_list = []
        with myserver.connection() as conn:
            logging.debug("Reached server %s", conn.server)
            attribute_list = list(attributes_to_query)
            entry_generator = conn.extend.standard.paged_search(search_base=myserver.base,
                                                                search_filter=mysearch.filter,
                                                                search_scope=myserver.ldap_scope,
                                                                attributes=attribute_list,
                                                                get_operational_attributes=True,
                                                                paged_size=10,
                                                                generator=True)
            # Keep a counter, so the non-dict object from conn.entries can be accessed
            # Other approach iterates entry in conn.response to access a dict version
            entry_counter = 0
            for entry in entry_generator:
                logging.info("Current entry (%d of %d): ==>\n%s\n<===",
                             (entry_counter + 1), len(conn.entries), entry)
                logging.info("LDIFoutput: ==>\n%s\n<===",
                             conn.entries[entry_counter].entry_to_ldif())
                # TODO: convert multi-value attributes presented as lists to output-friendly formats
                output_string = str(myoutput.output).format(dn=entry["dn"], **entry["attributes"])
                found_records_list.append(output_string)
                entry_counter += 1
        return found_records_list

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

        if u'filename' in kwargs:
            logging.debug("Config.filename=%s", kwargs[u'filename'])
            self._filename = kwargs["filename"]
            self._config = self.load_configuration(kwargs[u'filename'], encoding=self.encoding)
        logging.debug("_config=%s", self._config)

        # TODO: accept additional configs in kwargs
        for svc in self._config:
            logging.debug("Found top-level %s with name %s",
                          svc, self._config[svc][u'name'])
            service = self._config[svc]
            self.services_available[service[u'name']] = Service(name=service[u'name'],
                                                                server=service[u'server'],
                                                                searches=service[u'searches'],
                                                                outputs=service[u'outputs'])
            if not self.default_service or service[u'name'].get(u'is_default', False):
                self.default_service = service[u'name']

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
    def load_configuration(configuration_source, parent_configuration=None, encoding=u'utf-8'):
        """ Load configuration information from an external file

            :param configuration_source: filename containing the configuration, e.g., config.json
            :param parent_configuration: existing configuration the new file extends
            :param encoding: UTF encoding for the file
            :type configuration_source: string
            :type parent_configuration: dict
            :rtype: dict
        """
        assert configuration_source is not None
        if parent_configuration:
            config = parent_configuration
        else:
            config = dict()
        with codecs.open(configuration_source, u'r', encoding=encoding) as json_config_file:
            config = json.load(json_config_file)
        return config
