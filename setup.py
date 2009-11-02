from setuptools import setup

setup(
    name = 'tipfy',
    author = 'Rodrigo Moraes',
    author_email = 'rodrigo.moraes@gmail.com',
    url = 'http://code.google.com/p/tipfy/',
    description = 'The cute little framework for App Engine',
    license = 'BSD',
    version = '0.2',
    packages = ['tipfy'],
    package_dir = {'': 'source'},
    zip_safe = False,
    install_requires = ['werkzeug >= 0.6dev', 'jinja2', 'mako', 'babel'],
)
