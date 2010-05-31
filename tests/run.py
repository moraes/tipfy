# -*- coding: utf-8 -*-
# ----------------------------------
# Setup path and tipfy.ext namespace
import os
import sys

import nose

CURR_PATH = os.path.abspath(os.path.dirname(__file__))
APP_PATH  = os.path.abspath(os.path.join(CURR_PATH, '..', 'buildout', 'app'))

for path in [APP_PATH, CURR_PATH]:
    sys.path.insert(0, path)

ran = []


class TestLoader(nose.loader.TestLoader):
    def loadTestsFromDir(self, path):
        ran.append(path)
        return super(TestLoader, self).loadTestsFromDir(path)

        res = '*' * 200
        res += '\n'
        res += path
        res += '\n'
        res += '*' * 200
        sys.exit(res)

if __name__ == '__main__':
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
        'xmpp',
    ]

    argv = [__file__]

    argv += '-d --with-gae --without-sandbox --cover-erase --with-coverage --cover-package=tipfy --gae-application=../buildout/app'.split()

    paths = []
    #paths = ['./test_application.py', './test_config.py', './test_routing.py', './test_utils.py']
    paths = ['.']
    for ext in extensions:
        test_path = os.path.join('..', 'extensions', 'tipfy.ext.' + ext, 'tests')
        paths.append(test_path)

    #auth_path = os.path.join('..', 'extensions', 'tipfy.ext.auth', 'tests')
    #paths.append(os.path.join(auth_path, 'test_acl.py'))
    #paths.append(os.path.join(auth_path, 'test_auth.py'))
    #paths.append(os.path.join(auth_path, 'test_model.py'))

    argv += paths

    while len(ran):
        ran.pop()

    nose.run(argv=argv, testLoader=TestLoader)

    print '#' * 200
    print '\n'.join(ran)
