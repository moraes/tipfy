Tipfy Docs
==========

Tipfy uses Sphinx for documentation. The docs are written in ReStructuredText.

Quick references:

- http://sphinx.pocoo.org/
- http://docutils.sourceforge.net/rst.html

Building the docs
-----------------

1. Build the project so that Sphinx will have access to the API code: access
   the docs/project directory and run buildout::

       > cd docs/project
       > python2.5 bootstrap.py
       > bin/buildout
       > cd ../

2. Install sphinx (http://sphinx.pocoo.org/)::

       > sudo pip install sphinx

   or...::

       > sudo easy_install sphinx

   or (on Ubuntu)...::

       > sudo apt-get install python-sphinx

3. Build the docs::

       > make html


Rebuilding the docs
-------------------
To rebuild the docs, first clean the current build. Just do::

   > make clean
   > make html


Contributing
------------
Help on documentation is much needed and appreciated!

If you spot a typo or incorrect information in the docs, or think that
something can be improved, please let us know. You can use the mailing list
for this, or talk about it on IRC or, even better, clone the repo (on google
code, bitbucket or github), commit your fixes and then just tell us about it.

- Mailing list: http://groups.google.com/group/tipfy
- IRC channel: #tipfy @ freenode.org
- Project repositories:
  - http://code.google.com/p/tipfy/source/checkout
  - http://bitbucket.org/moraes/tipfy/
  - http://github.com/moraes/tipfy
