# -*- coding: utf-8 -*-
"""
    tipfy.scripting
    ~~~~~~~~~~~~~~~

    Scripting utilities.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import os
import sys


def set_gae_sys_path():
    """Sets sys.path including App Engine SDK and requirements."""
    base_path = os.getcwd()
    app_path = os.path.join(base_path, 'app')
    gae_path = os.path.join(base_path, 'var/parts/google_appengine')

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
