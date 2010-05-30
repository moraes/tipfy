"""
tipfy.ext.i18n
==============

"""
from setuptools import setup

setup(
    name = 'tipfy.ext.i18n',
    version = '1.0',
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
    include_package_data=True,
    install_requires = [
        'babel>=0.9.5',
        'Jinja2>=2.4',
        'werkzeug>=0.6.1',
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
