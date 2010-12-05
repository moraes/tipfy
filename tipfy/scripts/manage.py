#!/usr/bin/env python
import argparse
import ConfigParser
import os
import runpy
import shutil
import sys


class ArgumentParser(argparse.ArgumentParser):
    def parse_args(self, args=None, namespace=None, with_extras=False):
        """Parses arguments ignoring extra ones.

        :returns:
            If `with_extras` is False, the namespace populated with recognized
            arguments. Extra arguments will result in an error.

            If `with_extras` is True, a tuple (namespace, extra)  with the
            namespace populated with recognized arguments and a list with
            non-recognized ones.
        """
        if with_extras:
            return self.parse_known_args(args, namespace)

        return super(ArgumentParser, self).parse_args(args, namespace)


class Config(ConfigParser.RawConfigParser):
    """Wraps RawConfigParser `get*()` functions to allow a default to be
    returned instead of throwing errors. Also adds `getlist()` to split
    multi-line values into a list.
    """
    def get(self, section, option, default=None):
        return self._get_wrapper(self._get, section, option, default)

    def getboolean(self, section, option, default=None):
        return self._get_wrapper(self._getboolean, section, option, default)

    def getfloat(self, section, option, default=None):
        return self._get_wrapper(self._getfloat, section, option, default)

    def getint(self, section, option, default=None):
        return self._get_wrapper(self._getint, section, option, default)

    def getlist(self, section, option, default=None):
        return self._get_wrapper(self._getlist, section, option, default)

    def _get(self, section, option):
        return ConfigParser.RawConfigParser.get(self, section, option)

    def _getboolean(self, section, option):
        return ConfigParser.RawConfigParser.getboolean(self, section, option)

    def _getfloat(self, section, option):
        return ConfigParser.RawConfigParser.getfloat(self, section, option)

    def _getint(self, section, option):
        return ConfigParser.RawConfigParser.getint(self, section, option)

    def _getlist(self, section, option):
        value = self.get(section, option)
        values = []
        if value:
            for line in value.splitlines():
                line = line.strip()
                if line:
                    values.append(line)

        return values

    def _get_wrapper(self, get_func, section, option, default=None):
        """Wraps get functions allowing a default to be set."""
        try:
            return get_func(section, option)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError), e:
            return default


class Action(object):
    def __init__(self):
        pass

    def __call__(self, manager, argv):
        pass

    def error(self, message, status=1):
        sys.stderr.write(message)
        sys.stderr.write('\n')
        sys.exit(status)


class GaeSdkAction(Action):
    def __init__(self, action):
        self.action = action

    def __call__(self, manager, argv):
        sys.argv = [self.action] + argv
        try:
            runpy.run_module(self.action, run_name='__main__', alter_sys=True)
        except ImportError, e:
            # XXX explain that sys.path can be set on tipfy.cfg
            self.error("%s wasn't found. Add the App Engine SDK to "
                "sys.path." % self.action)


class InstallAppengineSdkAction(Action):
    def __init__(self):
        pass

    def __call__(self, manager, argv):
        pass


class CreateAppengineAppAction(Action):
    """Creates a directory for a new App Engine app. Usage::

        tipfy create_gae_app [template=/path/to/app/template] /path/to/new/app1

    A default app template is provided and used as skeleton if the template
    argument is not defined.
    """
    description = 'Creates a directory for a new App Engine app.'

    def __init__(self):
        tipfy_manage_dir = os.path.dirname(os.path.realpath(__file__))
        project_template = os.path.join(tipfy_manage_dir, 'gae_project')

        self.argparser = ArgumentParser(description=self.description)
        self.argparser.add_argument('project_dir', help='Project directory '
            'or directories.', nargs='+')
        self.argparser.add_argument('-t', '--template', dest='template',
            help='App template, copied to the new project directory. '
            'If not defined, the default app skeleton is used.',
            default=project_template)

    def __call__(self, manager, argv):
        args = self.argparser.parse_args(args=argv)

        # XXX if not set in args, try config before using default template.
        template_dir = os.path.abspath(args.template)
        if not os.path.exists(template_dir):
            self.error('Template directory not found: %s.' % template_dir)

        for project_dir in args.project_dir:
            self.create_project(project_dir, template_dir)

    def create_project(self, project_dir, template_dir):
        project_dir = os.path.abspath(project_dir)

        if os.path.exists(project_dir):
            self.error('Project directory already exists: %s.' % project_dir)

        shutil.copytree(template_dir, project_dir)


class RunserverAction(Action):
    def __init__(self):
        pass

    def __call__(self, manager, argv):
        pass


class DeployAction(Action):
    def __init__(self):
        pass

    def __call__(self, manager, argv):
        pass


class TipfyScript(object):
    description = 'Tipfy Management Utilities'

    actions = {
        # Wrappers for App Engine SDK tools.
        'appcfg':           GaeSdkAction('appcfg'),
        'bulkload_client':  GaeSdkAction('bulkload_client'),
        'bulkloader':       GaeSdkAction('bulkloader'),
        'dev_appserver':    GaeSdkAction('dev_appserver'),
        'remote_api_shell': GaeSdkAction('remote_api_shell'),
        'install_gae_sdk':  InstallAppengineSdkAction(),
        'create_gae_app':   CreateAppengineAppAction(),
        'runserver':        RunserverAction(),
        'deploy':           DeployAction(),
    }

    def __init__(self):
        actions = ', '.join(sorted(self.actions.keys()))
        self.argparser = ArgumentParser(description=self.description)
        self.argparser.add_argument('action', help='Action to perform. '
            'Available actions are: %s.' % actions)
        self.argparser.add_argument('-c', '--config', dest='config_file',
            help='Configuration file.')

    def __call__(self, argv):
        args, extras = self.argparser.parse_args(args=argv, with_extras=True)

        # Load configuration.
        self.parse_config(args.config_file)

        # Prepend configured paths to sys.path, if any.
        sys.path = self.config.getlist('setup', 'sys.path', []) + sys.path

        if args.action not in self.actions:
            # Unknown action.
            return self.argparser.print_help()

        self.actions[args.action](self, extras)

    def parse_config(self, config_files=None):
        """Load configuration. If files are not specified, try 'tipfy.cfg'
        in the current dir.
        """
        if config_files is None:
            config_files = os.path.join(os.getcwd(), 'tipfy.cfg')

        if not isinstance(config_files, list):
            config_files = [config_files]

        config_files = [os.path.abspath(f) for f in config_files]

        self.config = Config()
        self.config_files = self.config.read(config_files)


if __name__ == '__main__':
    manager = TipfyScript()
    manager(sys.argv[1:])
