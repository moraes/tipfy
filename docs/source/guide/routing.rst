.. _guide.routing:

URL Routing
===========

Quick Start
-----------
Define urls as a list of Rule instances in **urls.py**:

**urls.py**

.. code-block:: python

   from tipfy import Rule

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
TODO


Rule variables
~~~~~~~~~~~~~~
TODO


URL building
------------
TODO


Rule wrappers
-------------
When writing rules, sometimes the same arguments are repeated several times
for a group of URLs. There are several wrappers that help to reduce repetition.

HandlerPrefix
~~~~~~~~~~~~~
Used to add a common handler module prefix to a group of rules. For example,
all rules below use handlers stored in the module **my_module.my_handlers**:

**urls.py**

.. code-block:: python

   from tipfy import HandlerPrefix, Rule

   rules = [
       HandlerPrefix('my_module.my_handlers.', [
           Rule('/', name='home', handler='HomeHandler'),
           Rule('/about', name='about', handler='AboutHandler'),
           Rule('/contact', name='contact', handler='ContactHandler'),
       ]),
   ]

NamePrefix
~~~~~~~~~~
Used to add a common name prefix to a group of rules. For example, all rules
below use the prefix 'company-':

**urls.py**

.. code-block:: python

   from tipfy import NamePrefix, Rule

   rules = [
       NamePrefix('company-', [
           Rule('/', name='home', handler='handlers.HomeHandler'),
           Rule('/about', name='about', handler='handlers.AboutHandler'),
           Rule('/contact', name='contact', handler='handlers.ContactHandler'),
       ]),
   ]

So to generate URLs the name is 'company-home', 'company-about' and
'company-contact'. This is nice to prefix rule names belonging to a same
category or app.

Subdomain
~~~~~~~~~
TODO


Submount
~~~~~~~~
Used to add a common path prefix to a group of rules. For example, all rules
below are inside the path '/site':

**urls.py**

.. code-block:: python

   from tipfy import Rule, Submount

   rules = [
       Submount('/company', [
           Rule('/', name='home', handler='handlers.HomeHandler'),
           Rule('/history', name='about', handler='handlers.HistoryHandler'),
           Rule('/contact', name='contact', handler='handlers.ContactHandler'),
       ]),
   ]


Mixing Rule wrappers
~~~~~~~~~~~~~~~~~~~~
Rule wrappers can be mixed to prefix handler, name, path or subdomain as
needed. For example:

**urls.py**

.. code-block:: python

   from tipfy import NamePrefix, Rule, Submount

   rules = [
       Submount('/company', [
           NamePrefix('company-', [
               Rule('/', name='home', handler='handlers.HomeHandler'),
               Rule('/history', name='about', handler='handlers.HistoryHandler'),
               Rule('/contact', name='contact', handler='handlers.ContactHandler'),
           ]),
       ]),
   ]


Common solutions
----------------
TODO
