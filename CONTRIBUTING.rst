Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/cameronmaske/celery-once/issues.

If you are reporting a bug, please include:

-  Your operating system name and version.
-  Any details about your local setup that might be helpful in
   troubleshooting.
-  Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with “bug” is
open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

Celery Once could always use more documentation, whether as part of the
README, in docstrings, or even on the web in blog
posts, articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at
https://github.com/cameronmaske/celery-once/issues.

If you are proposing a feature:

-  Explain in detail how it would work.
-  Keep the scope as narrow as possible, to make it easier to implement.
-  Remember that this is a volunteer-driven project, and that
   contributions are welcome :)

Get Started!
~~~~~~~~~~~~

Ready to contribute? Here’s how to set up ``celery_once`` for local
development.

1. Fork the ``celery_once`` repo on GitHub.
2. Clone your fork locally::

   $ git clone git@github.com:your\_name\_here/celery-once.git

3. Install your local copy into a virtualenv. Assuming you have
   virtualenvwrapper installed, this is how you set up your fork for
   local development::

   $ mkvirtualenv celery-once
   $ cd celery-once/ $ pip install -e .
   $ pip install -r requirements-dev.txt

4. Create a branch for local development::

   $ git checkout -b name-of-your-bugfix-or-feature

Now you can make your changes locally.

5. When you’re done making changes, check that your changes using::

   $ py.test tests/

6. Commit your changes and push your branch to GitHub::

   $ git add .
   $ git commit -m “Your detailed description of your changes.”
   $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
~~~~~~~~~~~~~~~~~~~~~~~

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests. If you are not sure how to
   write the test and could use some guidance, mention that in the PR.
2. If the pull request adds functionality, the README.md doc should be
   updated.
3. The pull request should work for Python 2.7, 3.5 and 3.6. Check
   https://travis-ci.org/cameronmaske/celery-once/pull\_requests and make
   sure that the tests pass for all supported Python versions.

Tips
~~~~

To run a subset of tests::

    $ py.test

To run against python 2.7 and 3.3::

    $ tox
