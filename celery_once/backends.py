# -*- coding: utf-8 -*-

"""Definition of the supported caching backends."""

import importlib

import celery_once.tasks

try:
    from urlparse import urlparse
except ImportError:
    # Python 3!
    from urllib.parse import urlparse

from .helpers import now_unix


def get_backend(settings):
    backend_name = settings['backend']
    path = backend_name.split('.')
    backend_mod_name, backend_class_name = '.'.join(path[:-1]), path[-1]
    backend_mod = importlib.import_module(backend_mod_name)
    backend_class = getattr(backend_mod, backend_class_name)
    return backend_class(settings['settings'])


class Backend(object):

    """Base class for all backends.

    Each new backend must implement the following methods, using the
    logic specific to the backend itself:

    - raise_or_lock
    - clear_lock

    """

    def raise_or_lock(self, key, expires):
        """
        Checks if the task is locked and raises an exception, else locks
        the task.
        """
        pass

    def clear_lock(self, key):
        """Remove the lock from the cache."""
        pass


class Redis(Backend):

    """Redis backend."""

    def __init__(self, settings):
        from redis import StrictRedis
        self.details = self._parse_url(settings['url'])
        self.redis = StrictRedis(**self.details)

    @staticmethod
    def _parse_url(url):
        parsed = urlparse(url)
        details = {
            'host': parsed.hostname,
            'password': parsed.password,
            'port': parsed.port
        }
        try:
            details['db'] = int(parsed.path.lstrip('/'))
        except ValueError:
            pass
        return details

    def raise_or_lock(self, key, expires):
        """
        Checks if the task is locked and raises an exception, else locks
        the task.
        """
        now = now_unix()
        # Check if the tasks is already queued if key is in cache.
        result = self.redis.get(key)
        if result:
            # Work out how many seconds remaining till the task expires.
            remaining = int(result) - now
            if remaining > 0:
                raise celery_once.tasks.AlreadyQueued(remaining)

        # By default, the tasks and the key expire after 60 minutes.
        # (meaning it will not be executed and the lock will clear).
        self.redis.setex(key, expires, now + expires)

    def clear_lock(self, key):
        """Remove the lock from the cache."""
        return self.redis.delete(key)
