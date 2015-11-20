# -*- coding: utf-8 -*-
from celery import Task, states
from celery.result import EagerResult
from inspect import getcallargs
from .helpers import queue_once_key, get_redis, now_unix, cached_celery_property


class AlreadyQueued(Exception):
    def __init__(self, countdown):
        self.message = "Expires in {} seconds".format(countdown)
        self.countdown = countdown


class QueueOnce(Task):
    AlreadyQueued = AlreadyQueued
    once = {
        'graceful': False,
        'unlock_before_run': False,
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

    @cached_celery_property
    def redis(self):
        """
        Return a connection pool to redis.

        This property is cached at the celery app level, so that only the first
        executed QueueOnce task needs to instanciate a redis connection. The
        other ones will only re-use it.

        """
        return get_redis(
            getattr(self.config, "ONCE_REDIS_URL", "redis://localhost:6379/0"))

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
            self.raise_or_lock(key, once_timeout)
        except self.AlreadyQueued as e:
            if once_graceful:
                return EagerResult(None, None, states.REJECTED)
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
        # Remove the task instance from the kwargs. This only happens when the
        # task has the 'bind' attribute set to True. We remove it, as the task
        # has a memory pointer in its repr, that will change between the task
        # caller and the celery worker
        if isinstance(call_args.get('self'), Task):
            del call_args['self']
        key = queue_once_key(self.name, call_args, restrict_to)
        return key

    def raise_or_lock(self, key, expires):
        """
        Checks if the task is locked and raises an exception, else locks
        the task.
        """
        now = now_unix()
        # Check if the tasks is already queued if key is in redis.
        result = self.redis.get(key)
        if result:
            # Work out how many seconds remaining till the task expires.
            remaining = int(result) - now
            if remaining > 0:
                raise self.AlreadyQueued(remaining)

        # By default, the tasks and redis key expire after 60 minutes.
        # (meaning it will not be executed and the lock will clear).
        self.redis.setex(key, expires, now + expires)

    def get_unlock_before_run(self):
        return self.once.get('unlock_before_run', False)

    def __call__(self, *args, **kwargs):
        # Only clear the lock before the task's execution if the
        # "unlock_before_run" option is True
        if self.get_unlock_before_run():
            key = self.get_key(args, kwargs)
            self.clear_lock(key)

        return super(QueueOnce, self).__call__(*args, **kwargs)

    def clear_lock(self, key):
        self.redis.delete(key)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        After a task has run (both succesfully or with a failure) clear the
        lock if "unlock_before_run" is False.
        """
        # Only clear the lock after the task's execution if the
        # "unlock_before_run" option is False
        if not self.get_unlock_before_run():
            key = self.get_key(args, kwargs)
            self.clear_lock(key)
