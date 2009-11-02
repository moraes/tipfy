#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    manage

    Tipfy management utilities.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE for more details.
"""
import os, sys
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
    'source'))
LIB_DIR = os.path.join(PROJECT_DIR, 'lib')
sys.path.insert(0, LIB_DIR)
sys.path.insert(0, PROJECT_DIR)

import config
from werkzeug import script
from jinja2 import Environment
from compiler import compile_dir


def clear_dir(path):
    for dirname, subdirs, files in os.walk(path):
        for f in files:
            os.unlink(os.path.join(dirname, f))
        for d in subdirs:
            clear_dir(os.path.join(dirname, d))
            os.rmdir(os.path.join(dirname, d))


def action_precompile(basedir=('', '')):
    """Precompiles a whole templates directory located in basedir.

    Warning: the whole templates_compiled_dir will be erased before the new
    compilation.
    """
    # Apply jinja2 patches.
    import tipfy.ext.jinja2.patch

    if not config.templates_compiled_dir:
        raise ValueError('templates_compiled_dir is not defined in config')

    template_dir = os.path.join(basedir, config.templates_dir)
    compiled_dir = os.path.join(basedir, config.templates_compiled_dir)

    if not os.path.isdir(template_dir):
        raise ValueError('templates directory was not found in %s' %
            template_dir)

    # Empty compiled dir
    if os.path.isdir(compiled_dir):
        clear_dir(compiled_dir)
    else:
        os.mkdir(compiled_dir)

    env = Environment(extensions=['jinja2.ext.i18n'])
    compile_dir(env, template_dir, compiled_dir, as_module=True)


# Borrowed from Kay / app-engine-patch.
def setup_env():
    """Configures app engine environment for command-line apps."""
    # Try to import the appengine code from the system path.
    try:
        from google.appengine.api import apiproxy_stub_map
    except ImportError, e:
        # Not on the system path. Build a list of alternative paths where it
        # may be. First look within the project for a local copy, then look for
        # where the Mac OS SDK installs it.
        paths = [os.path.join(PROJECT_DIR, 'google_appengine'),
            '/usr/local/google_appengine']

        for path in os.environ.get('PATH', '').replace(';', ':').split(':'):
            path = path.rstrip(os.sep)
            if path.endswith('google_appengine'):
                paths.append(path)

        if os.name in ('nt', 'dos'):
            prefix = '%(PROGRAMFILES)s' % os.environ
            paths.append(prefix + r'\Google\google_appengine')

        # Loop through all possible paths and look for the SDK dir.
        SDK_PATH = None
        for sdk_path in paths:
            sdk_path = os.path.realpath(sdk_path)
            if os.path.exists(sdk_path):
                SDK_PATH = sdk_path
                break

        if SDK_PATH is None:
            # The SDK could not be found in any known location.
            sys.stderr.write('The Google App Engine SDK could not be found!')
            sys.exit(1)

        # Add the SDK and the libraries within it to the system path.
        EXTRA_PATHS = [SDK_PATH]
        lib = os.path.join(SDK_PATH, 'lib')

        # Automatically add all packages in the SDK's lib folder:
        for dir in os.listdir(lib):
            path = os.path.join(lib, dir)
            # Package can be under 'lib/<pkg>/<pkg>/' or 'lib/<pkg>/lib/<pkg>/'
            detect = (os.path.join(path, dir), os.path.join(path, 'lib', dir))
            for path in detect:
                if os.path.isdir(path):
                    EXTRA_PATHS.append(os.path.dirname(path))
                    break

        sys.path = EXTRA_PATHS + sys.path
        # corresponds with another google package

        if sys.modules.has_key('google'):
            del sys.modules['google']

        from google.appengine.api import apiproxy_stub_map


if __name__ == '__main__':
    setup_env()
    script.run()
