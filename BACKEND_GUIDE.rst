Contributing a new backend.
===========================

Contributing a new locking backend is greatly appreciated! Each new
backend must implement the following methods…

.. code:: python

    class Backend(object):
        """
        Each new backend must implement the following methods,
        - __init__
        - raise_or_lock
        - clear_lock
        """
        def __init__(self, settings):
            pass

        def raise_or_lock(self, key, timeout):
            pass

        def clear_lock(self, key):
            pass

``def raise_or_lock(self, key, timeout)``
-----------------------------------------

Checks if the task is locked based on the ``key`` argument (str). If
already locked should raise an ``AlreadyQueued`` exception. If not,
locks the task by the key. A ``timeout`` argument (int) can also be
passed in. The key should be cleared after the ``timeout`` (in seconds)
has passed.

``def clear_lock(self, key)``
-----------------------------

Removes the lock based on the ``key`` argument (str). This is called
after a task completes (either successfully, or fails beyond celery’s
retry limit).

``def __init__(self, settings)``
--------------------------------

The ``settings`` argument (dict) is based on the celery once
configuration. This can be used to setup the connection/client to the
backend. Any imports for backend specific modules should happen inside
here.

The `redis backend`_ is a good example of all of this in practice. If
you’d like to contribute a new backend and still feel unsure how to do
so, feel free to open an issue with any questions.

.. _redis backend: https://github.com/cameronmaske/celery-once/blob/dc1d679b6b12e2a26fafa6783bed0e54108336ce/celery_once/backends/redis.py#L32
