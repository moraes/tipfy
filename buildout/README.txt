Quick Start
===========

This is still barely documented. Here are some quick notes to get started:


Linux and Mac OS X
------------------

1. Access the buildout directory and call the bootstrap script using the
   Python 2.5 interpreter:

     $ python bootstrap.py


2. Build the project calling ./bin/buildout. This will download and setup
   tipfy and all dependencies, and create an app directory in ./parts/app.
   It may take a while.

     $ ./bin/buildout

   ...or, on Windows:

     $ bin\buildout


3. Start the development server localized in ./bin/dev_appserver pointing to
   the app directory:

     $ ./bin/dev_appserver ./parts/app/

   ...or, on Windows:

     $ python bin\dev_appserver parts\app


4. Open a browser and access the URLs:

     http://localhost:8080/
     http://localhost:8080/pretty


That's it. You now have a isolated development environment for your project.
