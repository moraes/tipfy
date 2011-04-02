Unit test setup
---------------
Run the tests inside a virtualenv. If you don't have it installed:

    $ pip install virtualenv

Then create a virtualenv inside the tests directory:

    $ cd path/to/tipfy/tests
    $ virtualenv env

Activate the virtualenv. On *nix:

    $ . env/bin/activate

...or on Windows:

    $ env\scripts\activate

Then install dependencies and libraries ued by the tests:

    $ pip install werkzeug
    $ pip install jinja2
    $ pip install blinker
    $ pip install babel
    $ pip install gaepytz
    $ pip install mako
    $ pip install coverage

Alternatively, install this compiled babel trunk for format_timedelta support:
http://tipfy.googlecode.com/files/babel_trunk_with_format_timedelta.tar.bz2

Uncompress, access the uncompressed dir, then:

    $ python setup.py install

Running the tests
-----------------
Activate the virtualenv. Then use the Makefile to run all tests (only tested
on Linux):

    $ make test

Or to run single tests:

    $ make app_test
    $ make config_test
    $ ...

Or to run the coverage:

    $ make coverage
