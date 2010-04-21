"""
tipfy.recipe.appengine
======================
This is a ZC Buildout recipe for setting up a
`Google App Engine <http://code.google.com/appengine/>`_ development
environment for the `tipfy <http://www.tipfy.org/>`_ framework.

Based on `rod.recipe.appengine <http://pypi.python.org/pypi/rod.recipe.appengine>`_

This fixes installation issues on Windows and adds an optional configuration to
install dependencies in a subdirectory of the app dir (e.g., '/app/lib').

It will eventually include specific features for tipfy.

Links
-----
* `Tipfy's website <http://www.tipfy.org/>`_
* `Documentation <http://www.tipfy.org//docs/>`_
"""
from setuptools import setup, find_packages


setup(
    name='tipfy.recipe.appengine',
    version='0.1.3',
    author='Rodrigo Moraes',
    author_email='rodrigo.moraes@gmail.com',
    description='ZC Buildout recipe for tipfy.',
    long_description=__doc__,
    license='LGPL 3',
    keywords='appengine gae zc.buildout recipe zope tipfy',
    url='http://pypi.python.org/pypi/tipfy.recipe.appengine',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Buildout',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'setuptools',
        'zc.buildout',
        'zc.recipe.egg',
    ],
    entry_points={'zc.buildout': ['default = tipfy.recipe.appengine:Recipe']},
    zip_safe=False,
)
