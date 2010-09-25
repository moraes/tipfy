# -*- coding: utf-8 -*-
"""
    tipfyext.jinja2.scripts
    ~~~~~~~~~~~~~~~~~~~~~~~

    Command line utilities for Jinja2.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import os
import sys

from jinja2 import FileSystemLoader

from tipfy import Tipfy
from tipfyext.jinja2 import Jinja2


def walk(top, topdown=True, onerror=None, followlinks=False):
    """Borrowed from Python 2.6.5 codebase. It is os.walk() with symlinks."""
    try:
        names = os.listdir(top)
    except os.error, err:
        if onerror is not None:
            onerror(err)
        return

    dirs, nondirs = [], []
    for name in names:
        if os.path.isdir(os.path.join(top, name)):
            if name != '_compiled':
                dirs.append(name)
        else:
            if name != '_compiled.zip':
                nondirs.append(name)

    if topdown:
        yield top, dirs, nondirs
    for name in dirs:
        path = os.path.join(top, name)
        if followlinks or not os.path.islink(path):
            for x in walk(path, topdown, onerror, followlinks):
                yield x
    if not topdown:
        yield top, dirs, nondirs


def list_templates(self):
    """Monkeypatch for FileSystemLoader to follow symlinks when searching for
    templates.
    """
    found = set()
    for searchpath in self.searchpath:
        for dirpath, dirnames, filenames in walk(searchpath, followlinks=True):
            for filename in filenames:
                template = os.path.join(dirpath, filename) \
                    [len(searchpath):].strip(os.path.sep) \
                                      .replace(os.path.sep, '/')
                if template[:2] == './':
                    template = template[2:]
                if template not in found:
                    found.add(template)
    return sorted(found)


def logger(msg):
    sys.stderr.write('%s\n' % msg)


def filter_templates(tpl):
    # Only ignore templates that start with '.'.
    return not os.path.basename(tpl).startswith('.')


def compile_templates(argv=None):
    """Compiles templates for better performance. This is a command line
    script. From the buildout directory, run:

        bin/jinja2_compile

    It will compile templates from the directory configured for 'templates_dir'
    to the one configured for 'templates_compiled_target'.

    At this time it doesn't accept any arguments.
    """
    if argv is None:
        argv = sys.argv

    cwd = os.getcwd()
    app_path = os.path.join(cwd, 'app')
    gae_path = os.path.join(cwd, 'var/parts/google_appengine')

    extra_paths = [
        app_path,
        gae_path,
        # These paths are required by the SDK.
        os.path.join(gae_path, 'lib', 'antlr3'),
        os.path.join(gae_path, 'lib', 'django'),
        os.path.join(gae_path, 'lib', 'ipaddr'),
        os.path.join(gae_path, 'lib', 'webob'),
        os.path.join(gae_path, 'lib', 'yaml', 'lib'),
    ]

    sys.path = extra_paths + sys.path

    from config import config

    app = Tipfy(config=config)
    cfg = app.get_config('tipfyext.jinja2')
    template_path = cfg.get('templates_dir')

    if cfg.get('use_zip_compiled'):
        compiled_target = os.path.join(template_path, '_compiled.zip')
        zip_cfg = 'deflated'
    else:
        compiled_target = os.path.join(template_path, '_compiled')
        zip_cfg = None

    if isinstance(template_path, basestring):
        # A single path.
        source = os.path.join(app_path, template_path)
    else:
        # A list of paths.
        source = [os.path.join(app_path, p) for p in template_path]

    target = os.path.join(app_path, compiled_target)

    # Set templates dir and deactivate compiled dir to use normal loader to
    # find the templates to be compiled.
    cfg['templates_dir'] = source
    cfg['use_compiled'] = False
    cfg['use_zip_compiled'] = False

    old_list_templates = FileSystemLoader.list_templates
    FileSystemLoader.list_templates = list_templates

    env = Jinja2.factory(app, 'jinja2').environment
    env.compile_templates(target, extensions=None, filter_func=filter_templates,
                          zip=zip_cfg, log_function=logger,
                          ignore_errors=False, py_compile=False)

    FileSystemLoader.list_templates = old_list_templates
