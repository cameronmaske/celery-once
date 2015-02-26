# -*- coding: utf-8 -*-

"""Definition of the supported caching backends."""

import celery_once.tasks

try:
    from urlparse import urlparse
except ImportError:
    # Python 3!
    from urllib.parse import urlparse

from .helpers import now_unix


def get_backend(backend_url):
    backends = {
        'redis': Redis,
    }
    backend_name = urlparse(backend_url).scheme
    return backends[backend_name](backend_url)


class Backend(object):

    """Base class for all backends.

    Each new backend must implement the following methods, using the
    logic specific to the backend itself:

    - get
    - set
    - set_expiry
    - delete

    """

    def raise_or_lock(self, key, expires):
        """
        Checks if the task is locked and raises an exception, else locks
        the task.
        """
        now = now_unix()
        # Check if the tasks is already queued if key is in cache.
        result = self.get(key)
        if result:
            # Work out how many seconds remaining till the task expires.
            remaining = int(result) - now
            if remaining > 0:
                raise celery_once.tasks.AlreadyQueued(remaining)

        # By default, the tasks and the key expire after 60 minutes.
        # (meaning it will not be executed and the lock will clear).
        self.set_expiry(key, expires, now + expires)

    def clear_lock(self, key):
        return self.delete(key)

    def get(self, key):
        raise NotImplementedError

    def set(self, key, value):
        raise NotImplementedError

    def set_expiry(self, key, expiry, value):
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError


class Redis(Backend):

    """Redis backend."""

    def __init__(self, url):
        from redis import StrictRedis
        self.details = self._parse_url(url)
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

    def get(self, key):
        return self.redis.get(key)

    def set(self, key, value):
        return self.redis.set(key, value)

    def set_expiry(self, key, expiry, value):
        return self.redis.setex(key, expiry, value)

    def delete(self, key):
        return self.redis.delete(key)
