# -*- coding: utf-8 -*-
from time import time
from redis import StrictRedis
try:
    from urlparse import urlparse
except:
    # Python 3!
    from urllib.parse import urlparse
import six


def parse_redis_details(url):
    parsed = urlparse(url)
    details = {
        'host': parsed.hostname,
        'password': parsed.password,
        'port': parsed.port
    }
    try:
        details['db'] = int(parsed.path.lstrip('/'))
    except:
        pass
    return details


def get_redis(url):
    return StrictRedis(**(parse_redis_details(url)))


def now_unix():
    """
    Returns the current time in UNIX time.
    """
    return int(time())


def convert_unicode_items_to_str(l):
    """
    Convert every binary type item (str in python 2, bytes in python 3)
    into text type (unicode in python 2, str in python 3).
    """
    for i, item in enumerate(l):
        if six.PY2:
            if isinstance(item, unicode):
                l[i] = item.encode('utf-8')
            elif isinstance(item, list):
                item = convert_unicode_items_to_str(item)
    return l


def kwargs_to_list(kwargs):
    """
    Turns {'a': 1, 'b': 2} into ["a-1", "b-2"]
    """
    kwargs_list = []
    # Kwargs are sorted in alphabetic order.
    # Taken from http://www.saltycrane.com/blog/2007/09/how-to-sort-python-dictionary-by-keys/
    for k, v in sorted(six.iteritems(kwargs), key=lambda kv: (str(kv[0]), str(kv[1]))):
        if isinstance(v, list):
            v = convert_unicode_items_to_str(v)
        kwargs_list.append(str(k) + '-' + str(v))
    return kwargs_list


def queue_once_key(name, kwargs, restrict_to=None):
    """
    Turns a list the name of the task, the kwargs and allowed keys
    into a redis key.
    """
    keys = ['qo', name]
    # Restrict to only the keys allowed in keys.
    if restrict_to is not None:
        restrict_kwargs = {key: kwargs[key] for key in restrict_to}
        keys += kwargs_to_list(restrict_kwargs)
    else:
        keys += kwargs_to_list(kwargs)
    key = "_".join(keys)
    return key
