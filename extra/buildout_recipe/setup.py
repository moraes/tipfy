"""Setup script."""
from setuptools import setup, find_packages


setup(
    name='tipfy.recipe.appengine',
    version='0.1',
    author='Rodrigo Moraes',
    author_email='rodrigo.moraes@gmail.com',
    description='ZC Buildout recipe for setting up a google appengine '
                'development environment using the tipfy framework. '
                'This is a slightly modified version of rod.recipe.appengine.',
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
