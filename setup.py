"""
Tipfy
=====
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
* `Documentation <http://www.tipfy.org//docs/>`_
"""
from setuptools import setup

setup(
    name = 'tipfy',
    version = '0.5.1',
    license = 'BSD',
    url = 'http://www.tipfy.org/',
    download_url = 'http://www.tipfy.org/downloads/tipfy.latest.tar.bz2',
    description = 'An almighty little framework made specifically for Google '
        'App Engine',
    long_description=__doc__,
    author = 'Rodrigo Moraes',
    author_email = 'rodrigo.moraes@gmail.com',
    zip_safe = False,
    platforms='any',
    package_dir = {'': 'source'},
    packages = [
        'tipfy',
        'tipfy.ext',
        'tipfy.ext.appstats',
        'tipfy.ext.auth',
        'tipfy.ext.blobstore',
        'tipfy.ext.db',
        'tipfy.ext.debugger',
        'tipfy.ext.i18n',
        'tipfy.ext.jinja2',
        'tipfy.ext.mako',
        'tipfy.ext.session',
        'tipfy.ext.taskqueue',
        'tipfy.ext.xmpp',
    ],
    install_requires = [
        'babel>=0.9.5',
        'Jinja2>=2.4',
        'werkzeug>=0.6.1',
        'WTForms>=0.5',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
