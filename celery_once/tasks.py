# -*- coding: utf-8 -*-

from inspect import getcallargs

from celery import Task

from .helpers import queue_once_key
from .backends import get_backend


class AlreadyQueued(Exception):

    def __init__(self, countdown):
        self.message = "Expires in {} seconds".format(countdown)
        self.countdown = countdown


class QueueOnce(Task):
    once = {
        'graceful': False,
    }

    """
    'There can be only one'. - Highlander (1986)

    An abstract tasks with the ability to detect if it has already been queued.
    When running the task (through .delay/.apply_async) it checks if the tasks
    is not already queued. By default it will raise an
    an AlreadyQueued exception if it is, by you can silence this by including
    `options={'graceful': True}` in apply_async or in the task's settings.

    Example:

    >>> from celery_queue.tasks import QueueOnce
    >>> from celery import task
    >>> @task(base=QueueOnce, once={'graceful': True})
    >>> def example(time):
    >>>     from time import sleep
    >>>     sleep(time)
    """
    abstract = True
    once = {}

    @property
    def config(self):
        app = self._get_app()
        return app.conf

    @property
    def once_backend(self):
        backend_url = (
            # kept for compatbility reasons
            getattr(self.config, "ONCE_REDIS_URL", None)
            # New generic config
            or getattr(self.config, "ONCE_BACKEND_URL", None)
            # default value
            or "redis://localhost:6379/0")
        return get_backend(backend_url)

    @property
    def default_timeout(self):
        return getattr(
            self.config, "ONCE_DEFAULT_TIMEOUT", 60 * 60)

    def apply_async(self, args=None, kwargs=None, **options):
        """
        Queues a task, raises an exception by default if already queued.

        :param \*args: positional arguments passed on to the task.
        :param \*\*kwargs: keyword arguments passed on to the task.
        :keyword \*\*once: (optional)
            :param: graceful: (optional)
                If True, wouldn't raise an exception if already queued.
                Instead will return none.
            :param: timeout: (optional)
                An `int' number of seconds after which the lock will expire.
                If not set, defaults to 1 hour.
            :param: keys: (optional)

        """
        once_options = options.get('once', {})
        once_graceful = once_options.get(
            'graceful', self.once.get('graceful', False))
        once_timeout = once_options.get(
            'timeout', self.once.get('timeout', self.default_timeout))

        key = self.get_key(args, kwargs)
        try:
            self.once_backend.raise_or_lock(key, once_timeout)
        except AlreadyQueued as e:
            if once_graceful:
                return None
            raise e
        return super(QueueOnce, self).apply_async(args, kwargs, **options)

    def get_key(self, args=None, kwargs=None):
        """
        Generate the key from the name of the task (e.g. 'tasks.example') and
        args/kwargs.
        """
        restrict_to = self.once.get('keys', None)
        args = args or {}
        kwargs = kwargs or {}
        call_args = getcallargs(self.run, *args, **kwargs)
        key = queue_once_key(self.name, call_args, restrict_to)
        return key

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        After a task has run (both succesfully or with a failure) clear the
        lock.
        """
        key = self.get_key(args, kwargs)
        self.once_backend.clear_lock(key)
