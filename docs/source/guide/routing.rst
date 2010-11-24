.. _guide.routing:

URL Routing
===========

Quick Start
-----------
Define urls as a list of Rule instances in **urls.py**:

**urls.py**

.. code-block:: python

   rules = [
       Rule('/', name='home', handler='handlers.HomeHandler'),
       Rule('/about', name='about', handler='handlers.AboutHandler'),
       Rule('/contact', name='contact', handler='handlers.ContactHandler'),
   ]


Then import it in **main.py** and use it to initialize the application:

**main.py**

.. code-block:: python

   from tipfy import Tipfy
   from urls import rules

   # Instantiate the application.
   app = Tipfy(rules=rules)

   def main():
       # Run the app.
       app.run()

   if __name__ == '__main__':
       main()


Anatomy of a Rule
-----------------

Rule parameters
~~~~~~~~~~~~~~~


Rule variables
~~~~~~~~~~~~~~


URL building
------------


Rule wrappers
-------------

HandlerPrefix
~~~~~~~~~~~~~


NamePrefix
~~~~~~~~~~


Subdomain
~~~~~~~~~


Submount
~~~~~~~~


Common solutions
----------------
