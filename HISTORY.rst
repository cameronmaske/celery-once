History
=======

3.0.1
-----
2019-08-21

Behind the scenes, changed how key's are generated from task function and arguments.
No longer uses ``inspect.getcallargs`` (deprecated) and is stored on ``__init__``.
Should fix issues if tasks are wrapped by other libraries (i.e. sentry-python).

3.0.0
-----
2019-05-13

Fixed an issue where large/long arguments could cause ``OSError Filename too long`` with the file backend (see #96).
Keys generated for file backend, are now hashed and limited to 50 characters in length.
*Due to this, it is not backwards compatible with existing keys from the file backend, so any pending locks from previous version will be ignored.*
The Redis backend is unchanged, and thus fully compatible.

Credit for fix to @xuhcc.

2.1.2
-----
2019-05-13

- Add support for ``rediss``. Thanks @gustavoalmeida

2.1.1
-----
2019-05-08

- Fix an issue with the ``File`` backend (#89) to close file after creation, else unclosed file descriptors eventually lead to an "Too many open files" error. Thanks @xuhcc.

2.1.0
-----
2019-02-25

- Added ``File`` backend (#84). Credit and thanks to @xuhcc.

2.0.1
-----
2019-02-25

- Fixed an issue when using ``autoretry_for`` with a task. (#74, #75). Thanks @pkariz.

2.0.0
-----

2018-04-25

Major Release:

This changes the Redis backend to use a SETNX-based lock (RedLock). This should address race conditions that the previous approach had (See: #7, #60).

*This may not be backwards compatible with existing keys stored in Redis.*
If you are upgrading from `1.0.0`, it may be safer to remove any previous used lock keys (See https://github.com/cameronmaske/celery-once/pull/67#issuecomment-384281438 for instructions).

Other changes include:

    - Able to run on blocking mode when scheduling tasks with Redis backend. See the README for more details.

    - ``AlreadyQueued`` exception return's countdown seconds as `float` instead of `int`.

Big thanks to @grjones for his contributions for this patch.


1.3.0
-----

2018-04-25

- Fixed an issue where tasks with autoretry_for got into a locked state (#58). Thanks @andbortnik.


1.2.0
-----

2017-06-12

- Cache the redis connection, instead of reinstantaiting one after each task execution (#34, #47). Thanks @brouberol.

1.1.0
-----

2017-06-12

- Exclude test files from package.
- Use relative import to import Redis backend. #52
- Correctly set `default_timeout` from settings. #53 #54 (Thanks @Snake575)

1.0.2
-----

2017-06-06

- Fixed an issue where retrying tasks would check for the lock on re-run (and error out). Thanks @lackita for the fix (#37, #48).


1.0.1
-----

2017-06-06

- Added support to connect to Redis over sockets. Thanks @brouberol (#33, #49)

1.0.0
-----

2017-06-05

Major release:

This release contains breaking changes. Please revisit the README for the latest setup instructions.

- Refactored code to allow for custom backends.
- Bumped offical support to celery >= 4.
- Bumped offical support to Python 2.7, 3.5 and 3.6.

0.1.4
-----

2015-07-29

Bugfixes:

- Fixed an issue where celery beat would crash on graceful enable tasks (#27).
Thanks @PhilipGarnero!

0.1.3
-----

2015-07-14

Features:

- Added option ``unlock_before_run`` to remove the lock before of after the task's execution. Thanks @jcugat!

0.1.2
-----

2015-03-15

Bugfixes:

- Standardized unicode/string handling for the name of a task when generating lock keys.

0.1.1
-----

2015-02-26

Bugfixes:

- Standardized unicode/string handling for keyword arguments when generating lock keys. #11
- Fixed an issue where self bound task (`bind=true`) would not correctly clear locks. #12

Thanks to @brouberol for contributions to both!

0.1
---

-  Initial release of PyPI
