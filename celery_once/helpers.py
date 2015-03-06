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


def force_string(kwargs):
    """
    Force key in dict or list to a string.
    Fixes: https://github.com/TrackMaven/celery-once/issues/11
    """
    if isinstance(kwargs, dict):
        return {
            force_string(key): force_string(value) for key, value in six.iteritems(kwargs)}
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
    for k, v in sorted(six.iteritems(kwargs), key=lambda kv: str(kv[0])):
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
