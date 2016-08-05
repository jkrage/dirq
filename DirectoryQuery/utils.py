#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    utils.py

    DirectoryQuery, utility functions

"""
import string


def get_format_fields(format_string):
    """ :type format_string: string.Formatter format_string

        Parse a string.format() format_string specification and extract
        any named fields that will be needed by the output.

        Ignore position-based (name is all numeric) and
        order-based/un-named fields (e.g., {}).

        This can be used to ensure those fields are available to the formatter
        prior to needing them.

        :rtype: set() of named fields
    """
    assert format_string is not None
    return set([f[1] for f in string.Formatter().parse(format_string)])


def get_named_format_fields(format_string):
    """ :type format_string: string.Formatter format_string

        Parse a string.format() format_string specification and extract
        any named fields that will be needed by the output.

        Ignore position-based (name is all numeric) and
        order-based/un-named fields (e.g., {}).

        This can be used to ensure those fields are available to the formatter
        prior to needing them.

        :rtype: set() of named fields
    """
    assert format_string is not None
    return set([f for f in get_format_fields(format_string) if f and not f.isnumeric()])
