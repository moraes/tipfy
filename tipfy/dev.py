# -*- coding: utf-8 -*-
"""
    tipfy.dev
    ~~~~~~~~~

    Development patches.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import sys

_ULTIMATE_SYS_PATH = None


def fix_sys_path():
    """A fix for issue 772. We must keep this here until it is fixed in the dev
    server.

    See: http://code.google.com/p/googleappengine/issues/detail?id=772
    """
    global _ULTIMATE_SYS_PATH
    if _ULTIMATE_SYS_PATH is None:
        _ULTIMATE_SYS_PATH = list(sys.path)
    elif sys.path != _ULTIMATE_SYS_PATH:
        sys.path[:] = _ULTIMATE_SYS_PATH
