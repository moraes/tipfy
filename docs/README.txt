Tipfy Docs
==========

The docs are in reStructuredText - http://docutils.sourceforge.net/docs/user/rst/quickstart.html

Building the docs
-----------------

1. Build the project: enter the docs/project directory and run buildout:

   > cd docs/project
   > python2.5 bootstrap.py --distribute
   > ./bin/buildout
   > cd ../

2. Install sphinx (http://sphinx.pocoo.org/):

   > sudo easy_install sphinx

3. Do the build:

   > make html


Rebuilding the docs
-------------------
To rebuild the docs, just do::

   > make clean
   > make html
