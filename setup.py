"""
Tipfy
=====
This is a tipfy experimental branch, which will be released as tipfy 0.7
in the future.

Tipfy is a small but powerful framework made specifically for
`Google App Engine <http://code.google.com/appengine/>`_. It is a lot like
`webapp <http://code.google.com/appengine/docs/python/tools/webapp/>`_::

    from tipfy import RequestHandler, Response

    class HelloWorldHandler(RequestHandler):
        def get(self):
            return Response('Hello, World!')


...but offers a bunch of features and goodies that webapp misses: i18n,
sessions, own authentication, flash messages and more. Everything in a modular,
lightweight way, tuned for App Engine. You use only what you need, when you
need.


Links
-----
* `Tipfy's website <http://www.tipfy.org/>`_
* `Installation instructions <http://www.tipfy.org/wiki/guide/installation/>`_
* `Extensions <http://www.tipfy.org/wiki/extensions/>`_
* `Wiki <http://www.tipfy.org/wiki/>`_
* `Discussion Group <http://groups.google.com/group/tipfy>`_
* `Issue Tracker <http://code.google.com/p/tipfy/issues/list>`_
* `Source Code Repository <http://code.google.com/p/tipfy/>`_
"""
from setuptools import setup

setup(
    name = 'tipfy-dev',
    version = '1.8',
    license = 'BSD',
    url = 'http://www.tipfy.org/',
    download_url = 'http://www.tipfy.org/tipfy.tar.gz',
    description = 'The almighty little framework for Google App Engine',
    long_description = __doc__,
    author = 'Rodrigo Moraes',
    author_email = 'rodrigo.moraes@gmail.com',
    zip_safe = False,
    platforms = 'any',
    packages = [
        'tipfy',
        'tipfy.appengine',
        'tipfy.appengine.auth',
        'tipfy.appengine.db',
        'tipfy.auth',
        'tipfy.debugger',
        'tipfyext',
        'tipfyext.appengine',
        'tipfyext.jinja2',
        'tipfyext.wtforms',
    ],
    namespace_packages = [
        'tipfyext',
        'tipfyext.appengine',
    ],
    include_package_data = True,
    install_requires = [
        'werkzeug>=0.6.1',
        # This is only required because a namespaced package is declated.
        'setuptools',
        'pip',
    ],
    extras_require = {
        'i18n': [
            'babel',
            'gaepytz',
        ],
        'jinja2': 'jinja2>=2.5.1',
        'wtforms': 'wtforms',
    },
    entry_points = {
        'console_scripts': [
            'jinja2_compile = tipfyext.jinja2.scripts:compile_templates',
            'tipfy = tipfy.scripts.manage:main',
        ],
    },
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
