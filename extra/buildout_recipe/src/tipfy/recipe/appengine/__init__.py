"""
Options:

sdk-dir: full path to the Google App Engine SDK in the system.
sdk-url: full URL to the Google App Engine SDK, to be downloaded.
app-directory: name of the app directory. Default is 'app'.
lib-directory: name of the app libraries directory. Default is 'app/lib'.
ext-directory: name of the app built libraries directory. Default is
    'app/lib/_build'.
etc-directory: Name of the directory to save extra stuff. Default is '/etc'.
downloads-directory = Name of the directory to save downloads. Default is
    '/etc/downloads'.
"""
import logging
import os
import sys
import shutil
import urllib
import zc.recipe.egg
import zipfile

logger = logging.getLogger(__name__)

is_win32 = (sys.platform == 'win32')

SERVER_SCRIPT = """#!%(python)s

import os
import sys

sys.path[0:0] = [
  %(sys_path)s
]

from dev_appserver import *

if __name__ == '__main__':
  os.environ['TMPDIR'] = r'%(var_dir)s'
  run_file(r'%(bin)s', locals())"""


APPCFG_SCRIPT = """#!%(python)s

import os
import sys

sys.path[0:0] = [
  %(sys_path)s
]

from appcfg import *

if __name__ == '__main__':
  run_file(r'%(bin)s', locals())"""


SYS_PATH_MODULE = '''# -*- coding: utf-8 -*-
"""
    _sys_path
    ~~~~~~~~~

    This is a generated module to set sys.path according to the buildout
    settings. Don't change it directly because it is overriden with a new
    build.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE for more details.
"""
import os
import sys

%(paths)s'''

LIB_README = """%(lib_dir)s
%(title_sub)s

Use this directory to place your libraries.

This directory is searched first when looking for a package, and
"%(ext_dir)s" is searched in sequence.

This directory is not editted by a build tool. It is a safe place for custom
libraries or to override packages from the "%(ext_dir)s" directory."""


DISTLIB_README = """Warning!
========

This directory is removed every time the build tool runs, so don't place or
edit things here because any changes will be lost!

Use the "%(lib_dir)s" directory to place other libraries or to override packages
from this directory."""


def copytree(src, dst, allowed_basenames=None, exclude=[]):
    """Local implementation of shutil's copytree function.

    Checks wheather destination directory exists or not
    before creating it.
    """
    if not os.path.isdir(src):
        # Assume that the egg's content is just one or more modules
        src = os.path.dirname(src)
        dst = os.path.dirname(dst)

    names = os.listdir(src)
    if not os.path.exists(dst):
        os.mkdir(dst)

    for name in names:
        base, ext = os.path.splitext(name)
        if ext == ".egg-info":
            continue

        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        if allowed_basenames:
            if os.path.isfile(srcname):
                if name not in allowed_basenames:
                    logger.debug("Skipped %s" % srcname)
                    continue

        if os.path.basename(srcname) in exclude:
            continue

        try:
            if os.path.isdir(srcname):
                copytree(srcname, dstname, allowed_basenames, exclude)
            else:
                shutil.copy2(srcname, dstname)
        except (IOError, os.error), why:
            logger.error("Can't copy %s to %s: %s" %
                          (srcname, dstname, str(why)))


class Recipe(zc.recipe.egg.Eggs):
    def __init__(self, buildout, name, opts):
        """Standard constructor for zc.buildout recipes."""
        super(Recipe, self).__init__(buildout, name, opts)

        join = os.path.join
        self.base_dir = join(self.buildout['buildout']['directory'])
        self.parts_dir = join(self.buildout['buildout']['parts-directory'])
        self.bin_dir = join(self.buildout['buildout']['bin-directory'])

        # Create all directories.
        # /app, /app/lib, /app/distlib
        app_dir = self.options.get('app-directory', 'app')
        lib_dir = self.options.get('lib-directory', join(app_dir, 'lib'))
        ext_dir = self.options.get('ext-directory', join(app_dir, 'distlib'))
        # /etc, /etc/downloads, /var
        etc_dir = self.options.get('etc-directory', 'etc')
        downloads_dir = self.options.get('downloads-directory', join(etc_dir,
            'downloads'))
        var_dir = self.options.get('var-directory', 'var')

        dirs = zip(
            ['app_dir', 'lib_dir', 'ext_dir', 'etc_dir', 'downloads_dir',
            'var_dir'],
            [app_dir, lib_dir, ext_dir, etc_dir, downloads_dir, var_dir])

        for name, value in dirs:
            path = join(self.base_dir, value)
            if not os.path.isdir(path):
                logger.info("Creating directory '%s'." % path)
                os.mkdir(path)

            setattr(self, name, path)

        # Create /lib/README.txt if not set yet.
        path = os.path.join(self.lib_dir, 'README.txt')
        if not os.path.isfile(path):
            lib_dir = self.lib_dir[len(self.app_dir):]
            ext_dir = self.ext_dir[len(self.app_dir):]
            content = LIB_README % {
                'lib_dir': lib_dir,
                'ext_dir': ext_dir,
                'title_sub': '=' * len(lib_dir)
            }

            script = open(path, 'w')
            script.write(content)
            script.close()


    def install(self):
        """Creates the part."""
        # Install packages.
        self.install_packages()
        # Install the Google App Engine SDK.
        self.install_sdk()
        # Install binary scripts.
        self.install_bin()

        return ()

    def update(self):
        """Updates the part."""
        # Install packages.
        self.install_packages()
        # Install the Google App Engine SDK.
        self.install_sdk()
        # Install binary scripts.
        self.install_bin()

        return ()

    def install_app_sys_path(self):
        """Install sys.path for the app."""
        dirs = [self.ext_dir, self.lib_dir]
        paths = []
        for d in dirs:
            d = d[len(self.app_dir):]
            parts = ["'%s'" % part for part in d.split(os.sep) if part.strip()]
            if len(parts) == 1:
                path = parts[0]
            else:
                path = 'os.path.join(%s)' % ', '.join(parts)

            paths.append('sys.path.insert(0, %s)' % path)

        content = SYS_PATH_MODULE % {'paths': '\n'.join(paths)}

        path = os.path.join(self.app_dir, '_sys_path.py')
        script = open(path, 'w')
        script.write(content.strip())
        script.close()

    def install_packages(self):
        reqs, ws = self.working_set()

        # Delete old dir and create it again.
        if os.path.isdir(self.ext_dir):
            logger.info("Deleting directory '%s'." % self.ext_dir)
            shutil.rmtree(self.ext_dir, True)

        logger.info("Creating directory '%s'." % self.ext_dir)
        os.mkdir(self.ext_dir)

        # Create README.txt.
        lib_dir = self.lib_dir[len(self.app_dir):]
        path = os.path.join(self.ext_dir, 'README.txt')
        script = open(path, 'w')
        script.write(DISTLIB_README % {'lib_dir': lib_dir})
        script.close()

        reqs, ws = self.working_set()

        packages = self.options.get('eggs', '').split()
        keys = [k.lower() for k in packages]
        for p in keys:
            if p not in ws.by_key.keys():
                raise KeyError, '%s: package not found.' % p

        entries = {}
        for k in ws.entry_keys:
            key = ws.entry_keys[k][0]
            if key in keys:
                entries[packages[keys.index(key)]] = k

        for key in entries.keys():
            top_level = os.path.join(ws.by_key[key]._provider.egg_info,
                                     'top_level.txt')
            top = open(top_level, 'r')
            top_dir = top.read()
            src = os.path.join(entries[key], top_dir.strip())
            top.close()
            dir = os.path.join(self.ext_dir, os.path.basename(src))
            egg_info_src = os.path.join(ws.by_key[key]._provider.egg_info,
                                        'SOURCES.txt')
            sources = open(egg_info_src, 'r')
            allowed_basenames = [os.path.basename(p.strip())
                                 for p in sources.readlines()]
            sources.close()
            if not os.path.exists(dir) and os.path.exists(src):
                os.mkdir(dir)

            # Exclude this every time
            exclude = ['EGG-INFO']
            copytree(src, dir, allowed_basenames=allowed_basenames,
                     exclude=exclude)

    def install_sdk(self):
        """Downloads and installs the Google App Engine SDK."""
        self.sdk_dir = self.options.get('sdk-dir')
        sdk_url = self.options.get('sdk-url')
        if not self.sdk_dir and not sdk_url:
            raise ValueError('You must define a value for "sdk-url" or '
                '"sdk-url" in buildout.cfg.')

        if self.sdk_dir:
            # Everything is set, so return.
            logger.info('Using Google App Engine SDK from %s' % self.sdk_dir)
            return

        # Set SDK dir to the one we wil fetch, and remove the old one.
        self.sdk_dir = os.path.join(self.parts_dir, 'google_appengine')
        if os.path.isdir(self.sdk_dir):
            shutil.rmtree(self.sdk_dir)

        # Extract the zip name: the last part of the path.
        filename = sdk_url.rsplit('/', 1)[-1]

        # Set the zip destination.
        dst = os.path.join(self.downloads_dir, filename)

        # Download the file if not yet downloaded.
        if not os.path.isfile(dst):
            logger.info('Downloading Google App Engine SDK...')
            urllib.urlretrieve(sdk_url, dst)
        else:
            logger.info('Google App SDK distribution already downloaded.')

        # Unzip the contents inside the parts dir.
        z = zipfile.ZipFile(dst)
        for f in z.namelist():
            if f.endswith('/'):
                os.mkdir(os.path.join(self.parts_dir, f))
            else:
                out = open(os.path.join(self.parts_dir, f), 'wb')
                out.write(z.read(f))
                out.close()

        if not os.path.isdir(self.sdk_dir):
            # At this point we must have a SDK.
            raise IOError('The Google App Engine SDK directory doesn\'t exist: '
                '%s' % self.sdk_dir)

    def install_bin(self):
        """Setup bin scripts."""
        # TODO: configurable script name is needed?
        # self.options.get('server-script', self.name)

        # Write server script.
        server = os.path.join(self.sdk_dir, 'dev_appserver.py')
        self.write_server_script('dev_appserver', server, [self.sdk_dir])

        # Write appcfg script.
        appcfg = os.path.join(self.sdk_dir, 'appcfg.py')
        self.write_appcfg_script(appcfg, [self.sdk_dir])

    def write_server_script(self, name, bin, sys_path):
        """Generates the development server script (dev_appserver) in bin."""
        # Generate script contents.
        content = SERVER_SCRIPT % {
            'python':   self.buildout[self.buildout['buildout']['python']]
                ['executable'],
            'sys_path': ',\n'.join(["    r'%s'" % p for p in sys_path]),
            'var_dir':  self.var_dir,
            'bin':      bin,
        }

        # Open the destination script file.
        path = os.path.join(self.bin_dir, name)
        script = open(path, 'w')
        script.write(content)
        script.close()
        os.chmod(path, 0755)

    def write_appcfg_script(self, bin, sys_path):
        """Generates the app configuration script (appcfg) in bin."""
        # Generate script contents.
        content = APPCFG_SCRIPT % {
            'python':   self.buildout[self.buildout['buildout']['python']]
                ['executable'],
            'sys_path': ',\n'.join(["  r'%s'" % p for p in sys_path]),
            'bin':      bin,
        }

        # Open the destination script file.
        path = os.path.join(self.bin_dir, 'appcfg')
        script = open(path, 'w')
        script.write(content)
        script.close()
        os.chmod(path, 0755)
