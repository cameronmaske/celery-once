# -*- coding: utf-8 -*-

"""Definition of the redis locking backend."""

from __future__ import absolute_import


try:
    from urlparse import urlparse
except ImportError:
    # Python 3!
    from urllib.parse import urlparse

from celery_once.helpers import now_unix
from celery_once.tasks import AlreadyQueued


def parse_url(url):
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


class Redis(object):
    """Redis backend."""

    def __init__(self, settings):
        try:
            from redis import StrictRedis
        except ImportError:
            raise ImportError(
                "You need to install the redis library in order to use Redis"
                " backend (pip install redis)")
        self._redis = StrictRedis(**parse_url(settings['url']))

    @property
    def redis(self):
        # Used to allow easy mocking when testing.
        return self._redis

    def raise_or_lock(self, key, timeout):
        """
        Checks if the task is locked and raises an exception, else locks
        the task.
        """
        now = now_unix()
        # Check if the tasks is already queued if key is in cache.
        result = self.redis.get(key)
        if result:
            # Work out how many seconds remaining till the task timeout.
            remaining = int(result) - now
            if remaining > 0:
                raise AlreadyQueued(remaining)

        # By default, the tasks and the key expire after 60 minutes.
        # (meaning it will not be executed and the lock will clear).
        self.redis.setex(key, timeout, now + timeout)

    def clear_lock(self, key):
        """Remove the lock from redis."""
        return self.redis.delete(key)
