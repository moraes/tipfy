"""
TODO: only use relative paths in /bin and any scripts.

Options:

sdk-dir: full path to the Google App Engine SDK in the system.
sdk-url: full URL to the Google App Engine SDK, to be downloaded.
app-directory: name of the app directory. Default is 'app'.
lib-directory: name of the app libraries directory. Default is 'app/lib'.
ext-directory: name of the app built libraries directory. Default is
    'app/lib/distlib'.
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

DEV_APPSERVER_SCRIPT = """#!%(python)s

import os
import sys

BASE = CURR_DIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
%(base)s
SDK_DIR = os.path.join(BASE, %(sdk)s)
SERVER_SCRIPT = os.path.join(SDK_DIR, 'dev_appserver.py')

sys.path[0:0] = [
  SDK_DIR,
]

from dev_appserver import *

def set_default_options():
  sys_path = list(sys.path)
  # Add the current path temporarily.
  sys.path.insert(0, CURR_DIR)

  from utils import get_dev_appserver_options

  config_file = os.path.abspath(os.path.join(os.path.dirname(__file__),
      'defaults.cfg'))
  argv = get_dev_appserver_options(sys.argv, config_file)
  if argv:
      sys.argv = argv

  # Remove temporary path.
  sys.path[:] = sys_path

if __name__ == '__main__':
  set_default_options()
  run_file(SERVER_SCRIPT, locals())"""


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


BIN_DEFAULTS_CFG = """[app]
path = %(app_path)s

[dev_appserver]
datastore_path = %(datastore_path)s
history_path = %(history_path)s
blobstore_path = %(blobstore_path)s"""


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

        # Write default config.
        self.write_bin_defaults_cfg()
        self.write_bin_utils()

    def write_server_script(self, name, bin, sys_path):
        """Generates the development server script (dev_appserver) in bin."""
        base = 'BASE = os.path.dirname(BASE)\n' * len(self.relpath(
            self.bin_dir))
        parts = self.relpath(self.parts_dir)
        parts.append('google_appengine')

        # Generate script contents.
        content = DEV_APPSERVER_SCRIPT % {
            'python':     self.buildout[self.buildout['buildout']['python']]
                ['executable'],
            'base': base.strip(),
            'sdk': ', '.join(["'%s'" % p for p in parts]),
            #'sys_path':   ',\n'.join(["  r'%s'" % p for p in sys_path]),
            #'utils_path': os.path.abspath(os.path.dirname(__file__)),
            #'bin':        bin,
        }

        # Save script file and chmod it.
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

        # Save script file and chmod it.
        path = os.path.join(self.bin_dir, 'appcfg')
        script = open(path, 'w')
        script.write(content)
        script.close()
        os.chmod(path, 0755)

    def write_bin_defaults_cfg(self):
        path = os.path.join(self.bin_dir, 'defaults.cfg')
        if os.path.isfile(path):
            # Don't overwrite it. It is editable by the user.
            return

        # Generate config contents.
        var_dir = self.var_dir[len(self.base_dir) + 1:]
        content = BIN_DEFAULTS_CFG % {
            'app_path':       os.path.basename(self.app_dir),
            'datastore_path': var_dir,
            'history_path':   var_dir,
            'blobstore_path': var_dir,
        }

        # Save config file.
        script = open(path, 'w')
        script.write(content)
        script.close()

    def write_bin_utils(self):
        path = os.path.join(self.bin_dir, 'utils.py')
        if os.path.isfile(path):
            # Don't overwrite it. It is editable by the user.
            return

        utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
            'utils.py'))

        # Save config file.
        script = open(path, 'w')
        script.write(file(utils_path).read())
        script.close()

    def relpath(self, path, basedir=None):
        """A very hackish implementation of os.path.relpath()."""
        basedir = basedir or self.base_dir
        if not path.startswith(basedir):
            raise ValueError('%s must be inside %s.' % (path, basedir))

        path = os.path.normpath(path[len(basedir):]).strip(os.path.sep)
        return path.split(os.path.sep)
