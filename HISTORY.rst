History
=======

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
