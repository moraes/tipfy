"""
tipfy.ext.wtforms
=================

This tipfy extension is a wrapper to `WTForms <http://wtforms.simplecodes.com/>`_
that provides better integration with tipfy's request object. For example,
input files are read from the form object, which is not supported by WTForms
because it is framework dependant.

The extension also provides builtin ReCaptcha support and will provide
CSRF protection in the future.

Documentation is available at
`http://www.tipfy.org/wiki/extensions/wtforms/ <http://www.tipfy.org/wiki/extensions/wtforms/>`_.

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
    name = 'tipfy.ext.wtforms',
    version = '0.5',
    license = 'BSD',
    url = 'http://www.tipfy.org/',
    description = 'WTForms extension for tipfy',
    long_description = __doc__,
    author = 'Rodrigo Moraes',
    author_email = 'rodrigo.moraes@gmail.com',
    zip_safe = False,
    platforms='any',
    packages = [
        'tipfy',
        'tipfy.ext',
        'tipfy.ext.wtforms',
    ],
    namespace_packages = [
        'tipfy',
        'tipfy.ext',
    ],
    include_package_data = True,
    install_requires = [
        'wtforms',
    ],
    classifiers = [
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
