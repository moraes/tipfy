Quick Installation
==================

Here are some quick notes to get started with tipfy. If you have problems,
follow the "Detailed Installation" instructions below.


1. Access the buildout directory and call the bootstrap script using your
   Python 2.5 interpreter:

     $ python bootstrap.py


2. Build the project calling bin/buildout. This will download and setup
   tipfy and all libraries inside the /app directory. It may take a while.

     $ bin/buildout


3. Start the development server calling bin/dev_appserver. It will use the
   application from /app by default:

     $ bin/dev_appserver


4. Open a browser and test the URLs:

     http://localhost:8080/
     http://localhost:8080/pretty


You should see a Hello, World. If you do, that's all. Now you have a project
environment to start developing your app.

Next step: read the API documentation and also the tutorials in tipfy's wiki:

- http://www.tipfy.org/docs/
- http://www.tipfy.org/wiki/


Detailed Installation
=====================

If you had problems in "Quick Installation", follow the steps below to setup
the basic requirements before you start.


Basic requirements
------------------

Before we setup Tipfy's environment, verify that you have installed in your
system:

  * Python 2.5
  * distribute (or setuptools)
  * pip (or easy_install)


If you don't have any of these, proceed to the instructions below.


Install Python 2.5
~~~~~~~~~~~~~~~~~~

Install Python 2.5 if you don't have it already. Google App Engine requires
version 2.5 and won't work properly if you use a different version. It must
be Python 2.5, not 2.4 or 2.6. We're repeating this because a lot of people
get stuck on weird problems later, only to realize that they should be using
Python 2.5 and not something else.

You can check which version you have typing in the command line::

    python --version


We won't cover Python 2.5 installation here; there are enough tutorials on
the web covering it for different systems. Go ahead and grab a good one.


Install a distutils library
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you don't have a distutils library (distribute or setuptools) installed on
you system yet, you need to install one. Distribute is recommended, but
anyone will serve.

Distribute is "the standard method for working with Python module
distributions". It will manage our package dependencies and upgrades.
The installation is straighforward:

1. Download the installer and save it anywhere. It is a single file::

     http://python-distribute.org/distribute_setup.py


2. Execute it using your Python 2.5 executable (this will require sudo if
   you are using a *nix system)::

     python distribute_setup.py


If you don't see any error messages, yay, it installed successfully. Let's
move forward.


Install a package installer
~~~~~~~~~~~~~~~~~~~~~~~~~~~

We need a package installer (pip or easy_install) to install and update our
libraries. Both will work, but if you don't have any yet, pip is recommended.
So let's install it:


1. Call easy_install to install it using your Python 2.5 executable (this
   will require sudo if you are using a *nix system)::

     easy_install pip


That's it. If no errors appear, we are good to go. Go back to "Quick
Installation" and follow those steps to install your environment.
