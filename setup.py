from setuptools import setup

setup(
    name = 'tipfy',
    author = 'Rodrigo Moraes',
    author_email = 'rodrigo.moraes@gmail.com',
    url = 'http://code.google.com/p/tipfy/',
    download_url = 'http://tipfy.googlecode.com/files/tipfy.latest.zip',
    description = 'The cute little framework for App Engine',
    license = 'BSD',
    version = '0.2',
    packages = ['tipfy'],
    package_dir = {'': 'source'},
    zip_safe = False,
    install_requires = ['werkzeug >= 0.6dev'],
    extras_require = {
        'Jinja2': ['jinja2'],
        'Mako':   ['mako'],
        'Babel':  ['badel'],
    },
)
