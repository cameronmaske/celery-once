# -*- coding: utf-8 -*-

"""Definition of helper functions."""

import operator
import six
import importlib
from collections import OrderedDict
from time import time


def import_backend(config):
    """
    Imports and initializes the Backend class.
    """
    backend_name = config['backend']
    path = backend_name.split('.')
    backend_mod_name, backend_class_name = '.'.join(path[:-1]), path[-1]
    backend_mod = importlib.import_module(backend_mod_name)
    backend_class = getattr(backend_mod, backend_class_name)
    return backend_class(config['settings'])


def items_sorted_by_key(kwargs):
    return sorted(six.iteritems(kwargs), key=operator.itemgetter(0))


def order_dict_to_string(d):
    return '{' + ', '.join(str(dict({x: y})).strip('{}') for x, y in d.items()) + '}'


def force_string(kwargs):
    """
    Force key in dict or list to a string.
    Fixes: https://github.com/cameronmaske/celery-once/issues/11
    """
    if isinstance(kwargs, dict):
        # Context: https://github.com/cameronmaske/celery-once/issues/58
        # Keep equivalent to string of dict for backwards compatibility.
        return order_dict_to_string(OrderedDict(
            (force_string(key), force_string(value))
            for key, value in items_sorted_by_key(kwargs)
        ))
    elif isinstance(kwargs, list):
        return [force_string(element) for element in kwargs]
    elif six.PY2 and isinstance(kwargs, unicode):
        return kwargs.encode('utf-8')
    return kwargs


def kwargs_to_list(kwargs):
    """
    Turns {'a': 1, 'b': 2} into ["a-1", "b-2"]
    """
    kwargs_list = []
    # Kwargs are sorted in alphabetic order by their keys.
    # Taken from http://www.saltycrane.com/blog/2007/09/how-to-sort-python-dictionary-by-keys/
    for k, v in items_sorted_by_key(kwargs):
        kwargs_list.append(str(k) + '-' + str(force_string(v)))
    return kwargs_list


def queue_once_key(name, kwargs, restrict_to=None):
    """
    Turns a list the name of the task, the kwargs and allowed keys
    into a redis key.
    """
    keys = ['qo', force_string(name)]
    # Restrict to only the keys allowed in keys.
    if restrict_to is not None:
        restrict_kwargs = {key: kwargs[key] for key in restrict_to}
        keys += kwargs_to_list(restrict_kwargs)
    else:
        keys += kwargs_to_list(kwargs)
    key = "_".join(keys)
    return key
