#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    manage

    Tipfy management utilities.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE for more details.
"""
import os, sys
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
    'source'))
libs_dir = os.path.join(root_dir, 'lib')
sys.path.insert(0, libs_dir)
sys.path.insert(0, root_dir)

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
    if not config.templates_compiled_dir:
        raise ValueError('templates_compiled_dir is not defined in config')

    template_dir = os.path.join(basedir, 'templates')
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


if __name__ == '__main__':
    script.run()
