.. _api.tipfy.config:

Configuration
=============
``app.yaml``, ``main.py``, ``config.py`` and ``urls.py`` are the basic files
used to configure and initialize a `Tipfy`_ application. In a common case,
you'll set ``app.yaml`` and ``main.py`` once (or use the provided ones, as they
cover common uses), and customize ``config.py`` and ``urls.py`` to fit your
application needs. We'll explain each one in details.


``app.yaml`` and ``main.py``
----------------------------
`Tipfy`_ comes with simple ``app.yaml`` and ``main.py`` files ready to be used
by any application. Unless you have uncommon needs, you can use them as they
are. About them:

  - ``app.yaml`` is a configuration file required by App Engine (read more
    about it in `app.yaml documentation`_)

  - ``main.py`` is used as the application "bootstrap": a file that receives
    requests and execute the appropriate application handlers.

You can use the provided ``main.py``, or you can set a bootstrap similar to it
in a different file, or even have multiple bootstrap files for apps configured
differently in the same project. The important part is to map each bootstrap
file in ``app.yaml``. In a simple (and common) approach, we map all requests
to ``main.py``, as in this example:

**app.yaml**

.. code-block:: yaml

   application: my-app
   version: 1
   runtime: python
   api_version: 1

   handlers:
   - url: /.*
     script: main.py


.. note::
   The default ``app.yaml`` that comes with `Tipfy`_ also defines handlers
   for remote API and deferred tasks. For simplicity they are not included in
   the example above.


``config.py``
-------------
By default, ``main.py`` will load configuration options from ``config.py``, to
pass the configuration dictionary that is set there to :func:`tipfy.make_wsgi_app`.

`Tipfy`_ uses a simple configuration system that let modules auto-configure
themselves. This means that no configuration is required in ``config.py``,
unless you **really want** to configure something.

The configuration dictionary is divided per module name, and each module
configuration is another dictionary. This makes it easy to find out which
configuration keys are available in the related module documentation. Also it
avoids collisions if two modules use the same configuration key. And finally
it allows modules to provide defaults for all configurable options, in most
cases making configuration entirely optional.

Let's show an example on how to configure the internationalization module,
``tipfy.ext.i18n``. We'll set the default locale to `pt_BR` and the default
timezone to `America/Sao_Paulo`. Pretty easy, see:

**config.py**

.. code-block:: python

   config = {}

   config['tipfy.ext.i18n'] = {
       # Change default values from the internalization module.
       'locale': 'pt_BR',
       'timezone': 'America/Sao_Paulo',
   }

Of course, you can set the config in smaller parts to make it more readable, if
you prefer. ;)

The nice thing is that modules can document their own configurable options, and
you can easily refer to their documentation for details. For example, all keys
used by ``tipfy`` and ``tipfy.ext.i18n`` are documented in their API pages: see
them :data:`here <tipfy.default_config>` and
:data:`here <tipfy.ext.i18n.default_config>`.

If any `Tipfy`_ module has configurable options, it is documented in the
module's ``default_config`` variable.

.. note::
   You don't need to set all configuration keys available for a module. You can
   define only the values that differs from the default values. All undefined
   keys will use the module's default values.


You can use this same configuration system for your own modules, acessing your
configurations using standard config functions from tipfy. `Tipfy`_  will
load default values from your custom module and make it uniformly accessible
in your app.


``urls.py``
-----------
All URLs in a `Tipfy`_ application are, by default, loaded from ``urls.py``.
This module must implement a ``get_rules()`` function that takes no parameters
and returns a list of :class:`tipfy.Rule` instances.

URL rules in tipfy are friendly and readable, as they don't use regular
expressions. Yet they are quite powerful.

.. note::
   :class:`tipfy.Rule` extends ``werkzeug.routing.Rule``, and works very much
   like it. For full details on how to set up URL rules and advanced options,
   please read the related chapter in the excellent
   `Werkzeug routing documentation`_.

Let's take a look at a set of rules defined for a blog application, borrowed
from `Werkzeug routing documentation`_:

**urls.py**

.. code-block:: python

   from tipfy import Rule

   def get_rules():
       return [
           Rule('/', endpoint='blog/index', handler='apps.blog:IndexHandler'),
           Rule('/<int:year>/', endpoint='blog/archive', handler='apps.blog:ArchiveHandler'),
           Rule('/<int:year>/<int:month>/', endpoint='blog/archive', handler='apps.blog:ArchiveHandler'),
           Rule('/<int:year>/<int:month>/<int:day>/', endpoint='blog/archive', handler='apps.blog:ArchiveHandler'),
           Rule('/<int:year>/<int:month>/<int:day>/<slug>', endpoint='blog/show_post', handler='apps.blog:PostHandler'),
           Rule('/feeds/', endpoint='blog/feeds', handler='apps.blog:FeedListHandler'),
           Rule('/feeds/<feed_name>.rss', endpoint='blog/show_feed', handler='apps.blog:FeedHandler'),
           Rule('/about', endpoint='blog/about_me', handler='apps.about:AboutHandler'),
       ]


Each application entry point has a rule defined in the list returned by
``get_rules()``. Rules use a special syntax to define variables: integers,
strings, paths and so on. When an URL matches one of these rules, these
variables are passed to the ``RequestHandler`` defined in the rule.

For example, take this rule:

.. code-block:: python

   Rule('/<int:year>/<int:month>/', endpoint='blog/archive', handler='apps.blog:ArchiveHandler'),


When the url ``/2009/11/`` is accessed, `Tipfy`_ will load the handler
``ArchiveHandler`` from the module ``apps.blog``, and pass the rule parameters
to the appropriate method. Let's define a simple ``ArchiveHandler`` as an
example:

**apps/blog.py**

.. code-block:: python

   from tipfy import RequestHandler, response

   class ArchiveHandler(RequestHandler):
       def get(self, **kwargs):
           response.data = 'This is year %d, and the month is %d!' % (
               kwargs['year'], kwargs['month'])
           return response


For the URL ``/2009/11/``, the above handler will print `This is year 2009,
and the month is 11!`.

To generate an URL using a given rule, use the function :func:`tipfy.url_for`.
For example, this creates an URL that maps to the ``ArchiveHandler`` class
above:

.. code-block:: python

   from tipfy import url_for

   url = url_for('blog/archive', year=2009, month=11)


There are several extra possibilities in the routing system, but this should be
the subject for a more advanced tutorial.


.. _Tipfy: http://code.google.com/p/tipfy/
.. _app.yaml documentation: http://code.google.com/appengine/docs/python/config/appconfig.html
.. _Werkzeug routing documentation: http://werkzeug.pocoo.org/documentation/dev/routing.html
