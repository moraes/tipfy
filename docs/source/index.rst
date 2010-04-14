.. _contents:

Welcome to Tipfy's documentation!
=================================
Tipfy is a small but powerful framework designed specifically for
`Google App Engine <http://code.google.com/appengine/>`_. It is a lot like
`webapp <http://code.google.com/appengine/docs/python/tools/webapp/>`_:

.. code-block:: python

   from tipfy import RequestHandler, Response

   class HelloWorldHandler(RequestHandler):
       def get(self):
           return Response('Hello, World!')


...but offers a lot of features (own authentication, sessions, i18n etc) and
other goodies that webapp misses. Everything in a modular, lightweight way,
tuned for App Engine. You use only what you need, when you need.

See also other `App Engine frameworks`_.


Tutorials
=========
.. toctree::
   :maxdepth: 1
   :glob:

   tutorials/*


API Reference
=============
.. toctree::
   :maxdepth: 3
   :glob:

   api/*

.. _tutorials:


Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _Tipfy: http://code.google.com/p/tipfy/
.. _Python: http://www.python.org/
.. _App Engine: http://code.google.com/appengine/
.. _web.py: http://webpy.org/
.. _webapp: http://code.google.com/appengine/docs/python/tools/webapp/
.. _Werkzeug: http://werkzeug.pocoo.org/
.. _App Engine frameworks: http://code.google.com/p/tipfy/wiki/AppEngineFrameworks
