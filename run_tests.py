# -*- coding: utf-8 -*-
# ----------------------------------
# Setup path and tipfy.ext namespace
import os
import sys

TIPFY_PATH = os.path.abspath(os.path.dirname(__file__))
APP_PATH = os.path.join(TIPFY_PATH, 'buildout', 'app')

for path in [TIPFY_PATH, APP_PATH]:
    if path not in sys.path:
        sys.path.insert(0, path)

extensions = [
    'appstats',
    'auth',
    'blobstore',
    'db',
    'debugger',
    'i18n',
    'jinja2',
    'mail',
    'mako',
    'session',
    'taskqueue',
    'xmpp'
]

for ext in extensions:
    path = os.path.join(TIPFY_PATH, 'extensions', 'tipfy.ext.' + ext)
    if path not in sys.path:
        sys.path.insert(0, path)

__import__('pkg_resources').declare_namespace('tipfy.ext')

# ----------------------------------

if __name__ == '__main__':
    paths = ['tests/']
    for ext in extensions:
        test_path = os.path.join('extensions', 'tipfy.ext.' + ext) + '/'
        paths.append(test_path)

    argv = [__file__] + ' -d --with-gae --without-sandbox --cover-erase --with-coverage --cover-package=tipfy --gae-application=./buildout/app'.split()
    argv += paths

    import nose
    nose.run(argv=argv)
