Celery Once
===========

|Build Status| |Coverage Status|

Celery Once allows you to prevent multiple execution and queuing of `celery <http://www.celeryproject.org/>`_ tasks.

Installation
============

Installing ``celery_once`` is simple with pip, just run:

::

    pip install -U celery_once


Requirements
============

* `Celery <http://www.celeryproject.org/>`_. Built to run with Celery 4.0. Older versions may work, but are not officially supported.

Usage
=====

To use ``celery_once``, your tasks need to inherit from an `abstract <http://celery.readthedocs.org/en/latest/userguide/tasks.html#abstract-classes>`_ base task called ``QueueOnce``.

Once installed, you'll need to configure a few options a ``ONCE`` key in celery's conf.

.. code:: python

    from celery import Celery
    from celery_once import QueueOnce
    from time import sleep

    celery = Celery('tasks', broker='amqp://guest@localhost//')
    celery.conf.ONCE = {
      'backend': 'celery_once.backends.Redis',
      'settings': {
        'url': 'redis://localhost:6379/0',
        'default_timeout': 60 * 60
      }
    }

    @celery.task(base=QueueOnce)
    def slow_task():
        sleep(30)
        return "Done!"


The exact configuration, depends on which locking backend you want to use. See [Backends](#Backends).


Behind the scenes, this overrides ``apply_async`` and ``delay``. It does not affect calling the tasks directly.

When running the task, ``celery_once`` checks that no lock is in place (against a Redis key).
If it isn't, the task will run as normal. Once the task completes (or ends due to an exception) the lock will clear.
If an attempt is made to run the task again before it completes an ``AlreadyQueued`` exception will be raised.

.. code:: python

    example.delay(10)
    example.delay(10)
    Traceback (most recent call last):
        ..
    AlreadyQueued()

.. code:: python

    result = example.apply_async(args=(10))
    result = example.apply_async(args=(10))
    Traceback (most recent call last):
        ..
    AlreadyQueued()


``graceful``
------------

Optionally, instead of raising an ``AlreadyQueued`` exception, the task can return ``None`` if ``once={'graceful': True}`` is set in the task's `options <http://celery.readthedocs.org/en/latest/userguide/tasks.html#list-of-options>`_ or when run through ``apply_async``.

.. code:: python

    from celery_once import AlreadyQueued
    # Either catch the exception,
    try:
        example.delay(10)
    except AlreadyQueued:
        pass
    # Or, handle it gracefully at run time.
    result = example.apply(args=(10), once={'graceful': True})
    # or by default.
    @celery.task(base=QueueOnce, once={'graceful': True})
    def slow_task():
        sleep(30)
        return "Done!"


``keys``
--------

By default ``celery_once`` creates a lock based on the task's name and its arguments and values.
Take for example, the following task below...

.. code:: python

    @celery.task(base=QueueOnce)
    def slow_add(a, b):
        sleep(30)
        return a + b

Running the task with different arguments will default to checking against different locks.

.. code:: python

    slow_add(1, 1)
    slow_add(1, 2)

If you want to specify locking based on a subset, or no arguments you can adjust the keys ``celery_once`` looks at in the task's `options <http://celery.readthedocs.org/en/latest/userguide/tasks.html#list-of-options>`_ with ``once={'keys': [..]}``

.. code:: python

    @celery.task(base=QueueOnce, once={'keys': ['a']})
    def slow_add(a, b):
        sleep(30)
        return a + b

    example.delay(1, 1)
    # Checks if any tasks are running with the `a=1`
    example.delay(1, 2)
    Traceback (most recent call last):
        ..
    AlreadyQueued()
    example.delay(2, 2)

.. code:: python

    @celery.task(base=QueueOnce, once={'keys': []})
    def slow_add(a, b):
        sleep(30)
        return a + b

    # Will enforce only one task can run, no matter what arguments.
    example.delay(1, 1)
    example.delay(2, 2)
    Traceback (most recent call last):
        ..
    AlreadyQueued()


``timeout``
-----------
As a fall back, ``celery_once`` will clear a lock after 60 minutes.
This is set globally in Celery's configuration with ``ONCE_DEFAULT_TIMEOUT`` but can be set for individual tasks using...

.. code:: python

    @celery.task(base=QueueOnce, once={'timeout': 60 * 60 * 10})
    def long_running_task():
        sleep(60 * 60 * 3)


``unlock_before_run``
---------------------
By default, the lock is removed after the task has executed (using celery's `after_return <https://celery.readthedocs.org/en/latest/reference/celery.app.task.html#celery.app.task.Task.after_return>`_). This behaviour can be changed setting the task's option ``unlock_before_run``. When set to ``True``, the lock will be removed just before executing the task.

**Caveats**:
  * Any retry of the task won't re-enable the lock!
  * This can only be set when defining the task, it cannot be passed dynamically to ``apply_async``

.. code:: python

    @celery.task(base=QueueOnce, once={'unlock_before_run': True})
    def slow_task():
        sleep(30)
        return "Done!"




Backends
========

Redis Backend
-------------


Requires:

* `Redis <http://redis.io/>`_ is used as a distributed locking mechanism.

Configuration:

-  ``backend`` - ``celery_once.backends.Redis``
-  ``settings``
  - ``default_timeout`` - how many seconds after a lock has been set before it should automatically timeout (defaults to 3600 seconds, or 1 hour).
  - ``url`` - should point towards a running Redis instance (defaults to ``redis://localhost:6379/0``). See below for the format options supported


The URL parser supports two patterns of urls:

* ``redis://host:port[/db][?options]``: redis over TCP

* ``redis+socket:///path/to/redis.sock[?options]``: redis over a UNIX socket

  The ``options`` query args are mapped to the `StrictRedis <https://redis-py.readthedocs.org/en/latest/index.html#redis.StrictRedis>`_ keyword args.
  Examples:
  * ``redis://localhost:6379/1``

  * ``redis+socket:///var/run/redis/redis.sock?db=1``


Example Configuration:

.. code:: python

    celery.conf.ONCE = {
      'backend': 'celery_once.backends.Redis',
      'settings': {
        'url': 'redis://localhost:6379/0',
        'default_timeout': 60 * 60
      }
    }


Custom Backend
--------------

If you want to implement a custom locking backend, see `BACKEND\_GUIDE.rst`_.

.. _BACKEND\_GUIDE.rst: BACKEND_GUIDE.rst

Support
=======

* Tests are run against Python 2.7, 3.4 and 3.5. Other versions may work, but are not officially supported.

Contributing
============

Contributions are welcome, and they are greatly appreciated! See `contributing
guide <CONTRIBUTING.rst>`_ for more details.


.. |Build Status| image:: https://travis-ci.org/TrackMaven/celery-once.svg
   :target: https://travis-ci.org/TrackMaven/celery-once
.. |Coverage Status| image:: https://coveralls.io/repos/TrackMaven/celery-once/badge.svg
   :target: https://coveralls.io/r/TrackMaven/celery-once
