"""
tipfy.ext.blobstore
===================

This extension provides request handlers to support PyAMF in tipfy, the
almighty little framework for Google App Engine.

PyAMF provides Action Message Format (AMF) support for Python that is
compatible with the Adobe Flash Player. See
`http://pyamf.org/ <http://pyamf.org/>`_ for details.

Links
-----
* `Tipfy's website <http://www.tipfy.org/>`_
* `API Documentation <http://www.tipfy.org/docs/>`_
* `Wiki <http://www.tipfy.org/wiki/>`_
* `Discussion Group <http://groups.google.com/group/tipfy>`_
* `Issue Tracker <http://code.google.com/p/tipfy/issues/list>`_
* `Repository <http://code.google.com/p/tipfy/>`_
"""
from setuptools import setup

setup(
    name = 'tipfy.ext.pyamf',
    version = '0.1',
    license = 'MIT',
    url = 'http://www.tipfy.org/',
    description = 'PyAMF extension for tipfy',
    long_description=__doc__,
    author = 'Rodrigo Moraes',
    author_email = 'rodrigo.moraes@gmail.com',
    zip_safe = False,
    platforms='any',
    packages = [
        'tipfy',
        'tipfy.ext',
    ],
    namespace_packages = [
        'tipfy',
        'tipfy.ext',
    ],
    include_package_data=True,
    install_requires = [
        'pyamf',
    ],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
