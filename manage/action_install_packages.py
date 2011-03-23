# -*- coding: utf-8 -*-
import datetime
import logging
import os
import shutil
import tempfile
import uuid

from z3c.recipe.scripts.scripts import Scripts

from appfy.recipe import (copytree, ignore_patterns, include_patterns,
    rmfiles, zipdir)


LIB_README = """Warning!
========

This directory is removed every time the buildout tool runs, so don't place
or edit things here because any changes will be lost!

Use a different directory for extra libraries instead of this one."""


class Recipe(Scripts):
    def __init__(self, buildout, name, opts):
        # Set a logger with the section name.
        self.logger = logging.getLogger(name)

        # Unzip eggs by default or we can't use some.
        opts.setdefault('unzip', 'true')

        self.eggs_dir = buildout['buildout']['eggs-directory']
        self.parts_dir = buildout['buildout']['parts-directory']
        self.temp_dir = os.path.join(self.parts_dir, 'temp')

        lib_dir = opts.get('lib-directory', 'distlib')
        self.lib_path = os.path.abspath(lib_dir)

        self.use_zip = opts.get('use-zipimport', 'false') == 'true'
        if self.use_zip:
            self.lib_path += '.zip'

        # Set list of globs and packages to be ignored.
        self.ignore_globs = [i for i in opts.get('ignore-globs', '') \
            .splitlines() if i.strip()]
        self.ignore_packages = [i for i in opts.get('ignore-packages', '') \
            .splitlines() if i.strip()]

        self.delete_safe = opts.get('delete-safe', 'true') != 'false'
        opts.setdefault('eggs', '')
        super(Recipe, self).__init__(buildout, name, opts)

    def install(self):
        # Get all installed packages.
        reqs, ws = self.working_set()
        paths = self.get_package_paths(ws)

        # For now we only support installing them in the app dir.
        # In the future we may support installing libraries in the parts dir.
        self.install_in_app_dir(paths)

        return super(Recipe, self).install()

    update = install

    def install_in_app_dir(self, paths):
        # Delete old libs.
        self.delete_libs()

        if self.use_zip:
            # Create temporary directory for the zip files.
            tmp_dir = os.path.join(tempfile.gettempdir(), uuid.uuid4().hex)
        else:
            tmp_dir = self.lib_path

        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)

        # Copy all files.
        for name, src in paths:
            if name in self.ignore_packages:
                # This package or module must be ignored.
                continue

            dst = os.path.join(tmp_dir, name)
            if not os.path.isdir(src):
                # Try single files listed as modules.
                src += '.py'
                dst += '.py'
                if not os.path.isfile(src) or os.path.isfile(dst):
                    continue

            self.logger.info('Copying %r...' % src)

            copytree(src, dst, os.path.dirname(src) + os.sep,
                ignore=ignore_patterns(*self.ignore_globs),
                logger=self.logger)

        # Save README.
        f = open(os.path.join(tmp_dir, 'README.txt'), 'w')
        f.write(LIB_README)
        f.close()

        if self.use_zip:
            # Zip file and remove temporary dir.
            zipdir(tmp_dir, self.lib_path)
            if os.path.isdir(tmp_dir):
                shutil.rmtree(tmp_dir)

    def get_package_paths(self, ws):
        """Returns the list of package paths to be copied."""
        pkgs = []
        for path in ws.entries:
            lib_paths = self.get_lib_paths(path)
            if not lib_paths:
                self.logger.info('Library not installed: missing egg info for '
                    '%r.' % path)
                continue

            for lib_path in lib_paths:
                pkgs.append((lib_path, os.path.join(path, lib_path)))

        return pkgs

    def get_top_level_libs(self, egg_path):
        top_path = os.path.join(egg_path, 'top_level.txt')
        if not os.path.isfile(top_path):
            return None

        f = open(top_path, 'r')
        libs = f.read().strip()
        f.close()

        # One lib per line.
        return [l.strip() for l in libs.splitlines() if l.strip()]

    def get_lib_paths(self, path):
        """Returns the 'EGG-INFO' or '.egg-info' directory."""
        egg_path = os.path.join(path, 'EGG-INFO')
        if os.path.isdir(egg_path):
            # Unzipped egg metadata.
            return self.get_top_level_libs(egg_path)

        if os.path.isfile(path):
            # Zipped egg? Should we try to unpack it?
            # unpack_archive(path, self.eggs_dir)
            return None

        # Last try: develop eggs.
        elif os.path.isdir(path):
            files = os.listdir(path)
            for filename in files:
                if filename.endswith('.egg-info'):
                    egg_path = os.path.join(path, filename)
                    return self.get_top_level_libs(egg_path)

    def delete_libs(self):
        """If the `delete-safe` option is set to true, move the old libraries
        directory to a temporary directory inside the parts dir instead of
        deleting it.
        """
        if not os.path.exists(self.lib_path):
            # Nothing to delete, so it is safe.
            return

        if self.delete_safe is True:
            # Move directory or zip to temporary backup directory.
            if not os.path.exists(self.temp_dir):
                os.makedirs(self.temp_dir)

            date = datetime.datetime.now().strftime('_%Y_%m_%d_%H_%M_%S')
            filename = os.path.basename(self.lib_path.rstrip(os.sep))
            if self.use_zip:
                filename = filename[:-4] + date + '.zip'
            else:
                filename += date

            dst = os.path.join(self.temp_dir, filename)
            shutil.move(self.lib_path, dst)
            self.logger.info('Saved libraries backup in %r.' % dst)
        else:
            # Simply delete the directory or zip.
            if self.use_zip:
                os.remove(self.lib_path)
                self.logger.info('Removed lib-zip %r.' % self.lib_path)
            else:
                # Delete the directory.
                shutil.rmtree(self.lib_path)
                self.logger.info('Removed lib-directory %r.' % self.lib_path)
