"""
tipfy.ext.auth.google
=====================

This extension provides an OpenId/Oauth authentication provider for Google.

Ported from `tornado.auth <http://github.com/facebook/tornado/blob/master/tornado/auth.py>`_.

Links
-----
* `Tipfy <http://www.tipfy.org/>`_
* `API Documentation <http://www.tipfy.org/docs/>`_
* `Wiki <http://www.tipfy.org/wiki/>`_
* `Discussion Group <http://groups.google.com/group/tipfy>`_
* `Issue Tracker <http://code.google.com/p/tipfy/issues/list>`_
* `Source Code Repository <http://code.google.com/p/tipfy/>`_
"""
from setuptools import setup

setup(
    name = 'tipfy.ext.auth.google',
    version = '0.1',
    license = 'Apache Software License',
    url = 'http://www.tipfy.org/',
    description = 'Google authentication extension for tipfy using OpenId/Oauth',
    long_description = __doc__,
    author = 'Rodrigo Moraes',
    author_email = 'rodrigo.moraes@gmail.com',
    zip_safe = False,
    platforms = 'any',
    packages = [
        'tipfy',
        'tipfy.ext',
        'tipfy.ext.auth',
    ],
    namespace_packages = [
        'tipfy',
        'tipfy.ext',
        'tipfy.ext.auth',
    ],
    include_package_data = True,
    install_requires = [
        'tipfy.ext.auth.oauth',
        'tipfy.ext.auth.openid',
    ],
    classifiers = [
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
