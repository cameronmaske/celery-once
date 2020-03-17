# -*- coding: utf-8 -*-

"""Definition of the sentinel locking backend."""

from __future__ import absolute_import

try:
    from redis.lock import Lock
except ImportError:
    raise ImportError(
        "You need to install the redis library in order to use Redis"
        " backend (pip install redis)"
    )

from celery_once.tasks import AlreadyQueued


class Sentinel(object):
    """Sentinel backend."""

    def __init__(self, settings):
        try:
            from redis.sentinel import Sentinel
        except ImportError:
            raise ImportError(
                "You need to install the redis library in order to use Redis"
                " backend (pip install redis)"
            )
        nodes = [
            (instance.split(":")[0], instance.split(":")[1])
            for instance in settings["instances"]
            if len(instance.split(":")) >= 2
        ]
        self._sentinel = Sentinel(nodes)
        self._master_name = settings.get("master_name")
        self._pass = settings.get("password")
        self._blocking_timeout = settings.get("default_timeout", 1)
        self._blocking = settings.get("blocking", False)

    @property
    def sentinel(self):
        # Used to allow easy mocking when testing.
        return self._sentinel

    def raise_or_lock(self, key, timeout):
        """
        Checks if the task is locked and raises an exception, else locks
        the task. By default, the tasks and the key expire after 60 minutes.
        (meaning it will not be executed and the lock will clear).
        """
        master = self.sentinel.master_for(
            self._master_name, password=self._pass, socket_timeout=0.1
        )
        acquired = Lock(
            master,
            key,
            timeout=timeout,
            blocking=self._blocking,
            blocking_timeout=self._blocking_timeout,
        ).acquire()

        if not acquired:
            # Time remaining in milliseconds
            # https://redis.io/commands/pttl
            ttl = master.pttl(key)
            raise AlreadyQueued(ttl / 1000.0)

    def clear_lock(self, key):
        """Remove the lock from redis."""
        master = self.sentinel.master_for(
            self._master_name, password=self._pass, socket_timeout=0.1
        )
        return master.delete(key)
