.. _api.tipfy.app:

Main App
========
.. module:: tipfy.app


RequestHandler
--------------
.. autoclass:: RequestHandler
   :members: middleware, __init__, __call__, auth, i18n, session,
             session_store, abort, get_config, get_valid_methods,
             handle_exception, make_response, redirect, redirect_to, url_for


Request and Response
--------------------
.. autoclass:: Request
   :members: url_adapter, rule, rule_args, json

.. autoclass:: Response


WSGI Application
----------------
.. autoclass:: Tipfy
   :members: allowed_methods, request_class, response_class, config_class,
             router_class, __init__, __call__, wsgi_app, handle_exception,
             make_response, get_config, get_test_client, get_test_handler, run,
             auth_store_class, i18n_store_class, session_store_class


Constants
---------
.. autodata:: SERVER_SOFTWARE
.. autodata:: APPLICATION_ID
.. autodata:: CURRENT_VERSION_ID
.. autodata:: DEV_APPSERVER
.. autodata:: APPENGINE


.. _Flask: http://flask.pocoo.org/
