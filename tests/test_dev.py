import unittest

from tipfy import Tipfy


class TestSysPath(unittest.TestCase):
    def test_ultimate_sys_path(self):
        """Mostly here to not be marked as uncovered."""
        from tipfy.dev import _ULTIMATE_SYS_PATH, fix_sys_path
        fix_sys_path()

    def test_ultimate_sys_path2(self):
        """Mostly here to not be marked as uncovered."""
        from tipfy.dev import _ULTIMATE_SYS_PATH, fix_sys_path
        _ULTIMATE_SYS_PATH = []
        fix_sys_path()

    def test_ultimate_sys_path3(self):
        """Mostly here to not be marked as uncovered."""
        import sys
        path = list(sys.path)
        sys.path = []

        from tipfy.dev import _ULTIMATE_SYS_PATH, fix_sys_path
        _ULTIMATE_SYS_PATH = []
        fix_sys_path()

        sys.path = path
