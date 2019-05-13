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

* `Celery <http://www.celeryproject.org/>`__. Built to run with Celery 4.0. Older versions may work, but are not officially supported.

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


The exact configuration, depends on which locking backend you want to use. See `Backends`_.


Behind the scenes, this overrides ``apply_async`` and ``delay``. It does not affect calling the tasks directly.

When running the task, ``celery_once`` checks that no lock is in place (against a Redis key).
If it isn't, the task will run as normal. Once the task completes (or ends due to an exception) the lock will clear.
If an attempt is made to run the task again before it completes an ``AlreadyQueued`` exception will be raised.

.. code-block:: python

    example.delay(10)
    example.delay(10)
    Traceback (most recent call last):
        ..
    AlreadyQueued()

.. code-block:: python

    result = example.apply_async(args=(10))
    result = example.apply_async(args=(10))
    Traceback (most recent call last):
        ..
    AlreadyQueued()


``graceful``
------------

Optionally, instead of raising an ``AlreadyQueued`` exception, the task can return ``None`` if ``once={'graceful': True}`` is set in the task's `options <http://celery.readthedocs.org/en/latest/userguide/tasks.html#list-of-options>`__ or when run through ``apply_async``.

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

* `Redis <http://redis.io/>`_ is used as a distributed locking mechanism. Behind the scenes, it use redis-py's `shared, distributed Lock <https://github.com/andymccurdy/redis-py/blob/31519e4ccef49fb59254ee5524007c81faa7e850/redis/lock.py#L8>`_.

Configuration:

-  ``backend`` - ``celery_once.backends.Redis``

-  ``settings``

  - ``default_timeout`` - how many seconds after a lock has been set before it should automatically timeout (defaults to 3600 seconds, or 1 hour).

  - ``url`` - should point towards a running Redis instance (defaults to ``redis://localhost:6379/0``). See below for the format options supported

  - ``blocking`` (boolean value: default ``False``) - If set to ``True``, scheduling a task (by ``.delay/.apply_async``) will block for X seconds to acquire the lock (see: ``blocking_timeout`` below). If no lock could be acquired after X seconds, will raise an ``AlreadyQueued`` exception. This is a very specific use-case scenario and by default is disabled.

  - ``blocking_timeout`` (int or float value: default ``1``) - How many seconds the task will block trying to aquire the lock, if ``blocking`` is set to ``True``. Setting this to ``None`` set's no timeout (equivalent to infinite seconds).



The URL parser supports three patterns of urls:

* ``redis://host:port[/db][?options]``: redis over TCP

* ``rediss://host:port[/db][?options]``: redis over TCP with SSL enabled.

* ``redis+socket:///path/to/redis.sock[?options]``: redis over a UNIX socket

  The ``options`` query args are mapped to the `StrictRedis <https://redis-py.readthedocs.org/en/latest/index.html#redis.StrictRedis>`_ keyword args.
  Examples:
  * ``redis://localhost:6379/1``
  
  * ``redis://localhost:6379/1?ssl=true``

  * ``rediss://localhost:6379/1``

  * ``redis+socket:///var/run/redis/redis.sock?db=1``


Example Configuration:

Minimal:

.. code:: python

    celery.conf.ONCE = {
      'backend': 'celery_once.backends.Redis',
      'settings': {
        'url': 'redis://localhost:6379/0',
        'default_timeout': 60 * 60
      }
    }


Advanced:
Scheduling tasks blocks up to 30 seconds trying to acquire a lock before raising an exception.

    .. code:: python

        celery.conf.ONCE = {
          'backend': 'celery_once.backends.Redis',
          'settings': {
            'url': 'redis://localhost:6379/0',
            'default_timeout': 60 * 60,
            'blocking': True,
            'blocking_timeout': 30
          }
        }

File Backend
-------------

Configuration:

-  ``backend`` - ``celery_once.backends.File``

-  ``settings``

  - ``location`` - directory where lock files will be located. Default is temporary directory.

  - ``default_timeout`` - how many seconds after a lock has been set before it should automatically timeout (defaults to 3600 seconds, or 1 hour).


Example Configuration:

.. code:: python

    celery.conf.ONCE = {
        'backend': 'celery_once.backends.File',
        'settings': {
            'location': '/tmp/celery_once',
            'default_timeout': 60 * 60
        }
    }


Flask Intergration
------------------
To avoid ``RuntimeError: Working outside of application context`` errors when using ``celery_once`` with `Flask <http://flask.pocoo.org/docs/1.0/>`_, you need to make the ``QueueOnce`` task base class application context aware.
If you've implemented Celery following the Flask `documentation <http://flask.pocoo.org/docs/1.0/patterns/celery/#configure>`_ you can extend it like so.

    .. code:: python

        def make_celery(app):
            celery = Celery(
                app.import_name,
                backend=app.config['CELERY_RESULT_BACKEND'],
                broker=app.config['CELERY_BROKER_URL']
            )
            celery.conf.update(app.config)

            class ContextTask(celery.Task):
                def __call__(self, *args, **kwargs):
                    with app.app_context():
                        return self.run(*args, **kwargs)
            celery.Task = ContextTask

            # Make QueueOnce app context aware.
            class ContextQueueOnce(QueueOnce):
                def __call__(self, *args, **kwargs):
                    with app.app_context():
                        return super(ContextQueueOnce, self).__call__(*args, **kwargs)

            # Attach to celery object for easy access.
            celery.QueueOnce = ContextQueueOnce
            return celery


Now, when instead of importing the ``QueueOnce`` base, you can use the context aware base on the ``celery`` object.

    .. code:: python

        celery = make_celery(app)

        @celery.task(base=celery.QueueOnce)
        def example_task(value):
            return


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


.. |Build Status| image:: https://travis-ci.org/cameronmaske/celery-once.svg
   :target: https://travis-ci.org/cameronmaske/celery-once
.. |Coverage Status| image:: https://coveralls.io/repos/cameronmaske/celery-once/badge.svg
   :target: https://coveralls.io/r/cameronmaske/celery-once
