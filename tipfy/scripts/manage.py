#!/usr/bin/env python
import ConfigParser
import os
import runpy
import shutil
import sys
import textwrap

import argparse


# Be a good neighbour.
if sys.platform == 'win32':
    GLOBAL_CONFIG_FILE = 'tipfy.cfg'
else:
    GLOBAL_CONFIG_FILE = '.tipfy.cfg'

MISSING_GAE_SDK_MSG = "%(script)r wasn't found. Add the App Engine SDK to " \
    "sys.path or configure sys.path in tipfy.cfg."


def import_string(import_name, silent=False):
    """Imports an object based on a string. If *silent* is True the return
    value will be None if the import fails.

    Simplified version of the function with same name from `Werkzeug`_. We
    duplicate it here because this file should not depend on external packages.

    :param import_name:
        The dotted name for the object to import.
    :param silent:
        If True, import errors are ignored and None is returned instead.
    :returns:
        The imported object.
    """
    if isinstance(import_name, unicode):
        return import_name.encode('utf-8')

    try:
        if '.' in import_name:
            module, obj = import_name.rsplit('.', 1)
            return getattr(__import__(module, None, None, [obj]), obj)
        else:
            return __import__(import_name)
    except (ImportError, AttributeError):
        if not silent:
            raise


def get_unique_sequence(seq):
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]


class ArgumentParser(argparse.ArgumentParser):
    def parse_args(self, args=None, namespace=None, with_extras=False):
        """Parses arguments ignoring extra ones.

        :returns:
            If `with_extras` is False, the namespace populated with recognized
            arguments. Extra arguments will result in an error.

            If `with_extras` is True, a tuple (namespace, extras)  with the
            namespace populated with recognized arguments and a list with the
            non-recognized arguments.
        """
        if with_extras:
            return self.parse_known_args(args, namespace)

        return super(ArgumentParser, self).parse_args(args, namespace)


class Config(ConfigParser.SafeConfigParser):
    """Wraps SafeConfigParser `get*()` functions to allow a default to be
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

    def getlist(self, section, option, default=None, unique=True):
        res = self._get_wrapper(self._getlist, section, option, default)
        if unique:
            return get_unique_sequence(res)

        return res

    def _get(self, section, option):
        return ConfigParser.SafeConfigParser.get(self, section, option)

    def _getboolean(self, section, option):
        return ConfigParser.SafeConfigParser.getboolean(self, section,
            option)

    def _getfloat(self, section, option):
        return ConfigParser.SafeConfigParser.getfloat(self, section, option)

    def _getint(self, section, option):
        return ConfigParser.SafeConfigParser.getint(self, section, option)

    def _getlist(self, section, option):
        value = self.get(section, option)
        res = []
        if value:
            for line in value.splitlines():
                line = line.strip()
                if line:
                    res.append(line)

        return res

    def _get_wrapper(self, get_func, sections, option, default=None):
        """Wraps get functions allowing default values and a list of sections
        looked up in order until a value is found.
        """
        if isinstance(sections, basestring):
            sections = [sections]

        for section in sections:
            try:
                if self._get(section, option) is not None:
                    return get_func(section, option)
            except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                pass
            except ConfigParser.InterpolationMissingOptionError:
                # XXX should check in the end if value for interpolation
                # was missing?
                pass

        return default


class Action(object):
    """Base interface for custom actions."""
    #: ArgumentParser description.
    description = None
    #: ArgumentParser epilog.
    epilog = None

    def __init__(self):
        pass

    def __call__(self, manager, argv):
        raise NotImplementedError()

    def error(self, message, status=1):
        """Displays an error message and exits."""
        self.message(message)
        sys.exit(status)

    def message(self, message):
        """Displays a message."""
        sys.stderr.write(message + '\n')

    def run_hooks(self, import_names, manager, args):
        """Executes a list of functions defined as strings. They are imported
        dynamically so their modules must be in sys.path. If any of the
        functions isn't found, none will be executed.
        """
        # Import all first.
        hooks = []
        for import_name in import_names:
            hook = import_string(import_name, True)
            if hook is None:
                self.error('Could not import %r.' % import_name)

            hooks.append(hook)

        # Execute all.
        for hook in hooks:
            hook(manager, args)


class CreateAppAction(Action):
    """Creates a directory for a new tipfy app."""
    description = 'Creates a directory for a new App Engine app.'

    def __init__(self):
        self.parser = ArgumentParser(description=self.description)
        self.parser.add_argument('app_dir', help='App directory '
            'or directories.', nargs='+')
        self.parser.add_argument('-t', '--template', dest='template',
            help='App template, copied to the new project directory. '
            'If not defined, the default app skeleton is used.')

    def __call__(self, manager, argv):
        args = self.parser.parse_args(args=argv)

        template_dir = args.template
        if not template_dir:
            # Try getting the template set in config.
            template_dir = manager.config.get(manager.config_section,
                'create_app.stubs.appengine')

        if not template_dir:
            # Use default template.
            curr_dir = os.path.dirname(os.path.realpath(__file__))
            template_dir = os.path.join(curr_dir, 'stubs', 'appengine')

        template_dir = os.path.abspath(template_dir)
        if not os.path.exists(template_dir):
            self.error('Template directory not found: %r.' % template_dir)

        for app_dir in args.app_dir:
            app_dir = os.path.abspath(app_dir)
            self.create_app(manager, app_dir, template_dir)

    def create_app(self, app_dir, template_dir):
        if os.path.exists(app_dir):
            self.error('Project directory already exists: %r.' % app_dir)

        shutil.copytree(template_dir, app_dir)

        # XXX Add section to config


class GaeSdkAction(Action):
    """This is just a wrapper for tools found in the Google App Engine SDK.
    No additional arguments are parsed.
    """
    def __init__(self, action):
        self.action = action

    def __call__(self, manager, argv):
        sys.argv = [self.action] + argv
        try:
            runpy.run_module(self.action, run_name='__main__', alter_sys=True)
        except ImportError:
            self.error(MISSING_GAE_SDK_MSG % dict(script=self.action))


class GaeSdkExtendedAction(Action):
    action = None
    options = []

    def get_option_config_key(self, option):
        raise NotImplementedError()

    def get_base_gae_argv(self):
        raise NotImplementedError()

    def get_getopt_options(self):
        for option in self.options:
            if isinstance(option, tuple):
                long_option, short_option = option
            else:
                long_option = option
                short_option = None

            is_bool = not long_option.endswith('=')
            long_option = long_option.strip('=')

            yield long_option, short_option, is_bool

    def get_parser_from_getopt_options(self, manager):
        section = manager.config_section

        usage = '%%(prog)s %(action)s [--config CONFIG] [--app APP] ' \
            '[options]' % dict(action=self.action)

        parser = ArgumentParser(
            description=self.description,
            add_help=False,
            usage=usage,
            formatter_class=argparse.RawDescriptionHelpFormatter)

        for long_option, short_option, is_bool in self.get_getopt_options():
            option = self.get_option_config_key(long_option)
            args = ['--%s' % long_option]
            kwargs = {}

            if short_option:
                args.append('-%s' % short_option)

            if is_bool:
                kwargs['action'] = 'store_true'
                kwargs['default'] = manager.config.getboolean(section, option)
            else:
                kwargs['default'] = manager.config.get(section, option)

            parser.add_argument(*args, **kwargs)

        # Add app path.
        app_path = manager.config.get(section, 'path', '')
        parser.add_argument('app', nargs='?', default=app_path)

        return parser

    def get_gae_argv(self, manager, argv):
        parser = self.get_parser_from_getopt_options(manager)
        args, extras = parser.parse_args(args=argv, with_extras=True)

        if args.help:
            parser.print_help()
            sys.exit(1)

        gae_argv = self.get_base_gae_argv()
        for long_option, short_option, is_bool in self.get_getopt_options():
            value = getattr(args, long_option)
            if value is not None:
                if is_bool and value:
                    value = '--%s' % long_option
                elif not is_bool:
                    value = '--%s=%s' % (long_option, value)

                if value:
                    gae_argv.append(value)

        # Add app path.
        gae_argv.append(os.path.abspath(args.app))

        return gae_argv


class GaeRunserverAction(GaeSdkExtendedAction):
    """
    A convenient wrapper for "dev_appserver": starts the Google App Engine
    development server using before and after hooks and allowing configurable
    defaults.

    Each option can be defined in tipfy.cfg in the main section or for
    a specific app, prefixed by "runserver.":

        [DEFAULT]
        runserver.debug = true
        runserver.datastore_path = /path/to/%(app_key)s.datastore

        [app:my_app]
        app_key = my_app
        path = /path/to/app
        runserver.port = 8081

    In this case, executing:

        tipfy runserver --app=my_app

    ...will expand to:

        dev_appserver --datastore_path=/path/to/my_app.datastore --debug --port=8081 /path/to/app

    Define in "runserver.before" and "runserver.after" a list of functions
    to run before and after the server executes. These functions are imported
    so they must be in sys.path. For example:

        [DEFAULT]
        runserver.before =
            hooks.before_runserver_1
            hooks.before_runserver_2

        runserver.after =
            hooks.after_runserver_1
            hooks.after_runserver_2

    Then define in the module "hooks.py" some functions to be executed:

        def before_runserver_1(manager, args):
            print 'before_runserver_1!'

        def after_runserver_1(manager, args):
            print 'after_runserver_1!'

        # ...

    Use "tipfy dev_appserver --help" for a description of each option.
    """
    description = textwrap.dedent(__doc__)

    action = 'runserver'

    # All options from dev_appserver in a modified getopt style.
    options = [
        ('address=', 'a'),
        'admin_console_server=',
        'admin_console_host=',
        'allow_skipped_files',
        'auth_domain=',
        ('clear_datastore', 'c'),
        'blobstore_path=',
        'datastore_path=',
        'use_sqlite',
        ('debug', 'd'),
        'debug_imports',
        'enable_sendmail',
        'disable_static_caching',
        'show_mail_body',
        ('help', 'h'),
        'history_path=',
        'mysql_host=',
        'mysql_port=',
        'mysql_user=',
        'mysql_password=',
        ('port=', 'p'),
        'require_indexes',
        'smtp_host=',
        'smtp_password=',
        'smtp_port=',
        'smtp_user=',
        'disable_task_running',
        'task_retry_seconds=',
        'template_dir=',
        'trusted',
    ]

    def get_option_config_key(self, option):
        return 'runserver.%s' % option

    def get_base_gae_argv(self):
        return ['dev_appserver']

    def __call__(self, manager, argv):
        section = manager.config_section
        before_hooks = manager.config.getlist(section, 'runserver.before', [])
        after_hooks = manager.config.getlist(section, 'runserver.after', [])

        # Assemble arguments.
        sys.argv = self.get_gae_argv(manager, argv)

        # Execute runserver.before scripts.
        self.run_hooks(before_hooks, manager, argv)

        try:
            self.message('Executing: %s' % ' '.join(sys.argv))
            return
            runpy.run_module('dev_appserver', run_name='__main__',
                alter_sys=True)
        except ImportError:
            self.error(MISSING_GAE_SDK_MSG % dict(script='dev_appserver'))
        finally:
            # Execute runserver.after scripts.
            self.run_hooks(after_hooks, manager, argv)


class GaeDeployAction(GaeSdkExtendedAction):
    """
    A convenient wrapper for "appcfg update": deploys to Google App Engine
    using before and after hooks and allowing configurable defaults.

    Each option can be defined in tipfy.cfg in the main section or for
    a specific app, prefixed by "deploy.":

        [DEFAULT]
        deploy.verbose = true

        [app:my_app]
        path = /path/to/app
        deploy.email = user@gmail.com
        deploy.no_cookies = true

    In this case, executing:

        tipfy deploy --app=my_app

    ...will expand to:

        appcfg update --verbose --email=user@gmail.com --no_cookies /path/to/app

    Define in "deploy.before" and "deploy.after" a list of functions to run
    before and after deployment. These functions are imported so they must
    be in sys.path. For example:

        [DEFAULT]
        deploy.before =
            hooks.before_deploy_1
            hooks.before_deploy_2

        deploy.after =
            hooks.after_deploy_1
            hooks.after_deploy_2

    Then define in the module "hooks.py" some functions to be executed:

        def before_deploy_1(manager, args):
            print 'before_deploy_1!'

        def after_deploy_1(manager, args):
            print 'after_deploy_1!'

        # ...

    Use "tipfy appcfg update --help" for a description of each option.
    """
    description = textwrap.dedent(__doc__)

    action = 'deploy'

    # All options from appcfg update in a modified getopt style.
    options = [
      ('help', 'h'),
      ('quiet', 'q'),
      ('verbose', 'v'),
      'noisy',
      ('server=', 's'),
      'insecure',
      ('email=', 'e'),
      ('host=', 'H'),
      'no_cookies',
      'passin',
      ('application=', 'A'),
      ('version=', 'V'),
      ('max_size=', 'S'),
      'no_precompilation',
    ]

    def get_option_config_key(self, option):
        return 'deploy.%s' % option

    def get_base_gae_argv(self):
        return ['appcfg', 'update']

    def __call__(self, manager, argv):
        section = manager.config_section
        before_hooks = manager.config.getlist(section, 'deploy.before', [])
        after_hooks = manager.config.getlist(section, 'deploy.after', [])

        # Assemble arguments.
        sys.argv = self.get_gae_argv(manager, argv)

        # Execute deploy.before scripts.
        self.run_hooks(before_hooks, manager, argv)

        try:
            self.message('Executing: %s' % ' '.join(sys.argv))
            runpy.run_module('appcfg', run_name='__main__',
                alter_sys=True)
        except ImportError:
            self.error(MISSING_GAE_SDK_MSG % dict(script='appcfg'))
        finally:
            # Execute deploy.after scripts.
            self.run_hooks(after_hooks, manager, argv)


class InstallPackageAction(Action):
    description = 'Installs packages in the app directory.'

    def __init__(self):
        # XXX cache option
        # XXX symlinks option
        self.parser = ArgumentParser(description=self.description)
        self.parser.add_argument('packages', help='Package names', nargs='+')
        self.parser.add_argument('app_dir', help='App directory.')

    def __call__(self, manager, argv):
        args = self.parser.parse_args(args=argv)


class InstallAppengineSdkAction(Action):
    """Not implemented yet."""
    description = 'Downloads and unzips the App Engine SDK.'

    def __init__(self):
        self.parser = ArgumentParser(description=self.description)
        self.parser.add_argument('--version', '-v', help='SDK version. '
            'If not defined, downloads the latest stable one.')

    def __call__(self, manager, argv):
        raise NotImplementedError()


class TestAction(Action):
    """Testing stuff."""
    def __call__(self, manager, argv):
        print manager.app


class TipfyManager(object):
    description = 'Tipfy Management Utilities.'
    epilog = 'Use "%(prog)s action --help" for help on specific actions.'

    # XXX Allow users to hook in custom actions.
    actions = {
        # Wrappers for App Engine SDK tools.
        'appcfg':           GaeSdkAction('appcfg'),
        'bulkload_client':  GaeSdkAction('bulkload_client'),
        'bulkloader':       GaeSdkAction('bulkloader'),
        'dev_appserver':    GaeSdkAction('dev_appserver'),
        'remote_api_shell': GaeSdkAction('remote_api_shell'),
        # For now these are App Engine specific.
        'runserver':        GaeRunserverAction(),
        'deploy':           GaeDeployAction(),
        # Extra ones.
        # 'install_gae_sdk':  InstallAppengineSdkAction(),
        'create_app':       CreateAppAction(),
        'install':          InstallPackageAction(),
        'test':             TestAction(),
    }

    def __init__(self):
        actions = ', '.join(sorted(self.actions.keys()))
        self.parser = ArgumentParser(description=self.description,
            epilog=self.epilog, add_help=False)
        self.parser.add_argument('action', help='Action to perform. '
            'Available actions are: %s.' % actions, nargs='?')
        self.parser.add_argument('--config', default='tipfy.cfg',
            help='Configuration file.')
        self.parser.add_argument('--app', help='App configuration to load.')
        self.parser.add_argument('-h', '--help', help='Show this help message '
            'and exit.', action='store_true')

    def __call__(self, argv):
        args, extras = self.parser.parse_args(args=argv, with_extras=True)

        # Load configuration.
        self.parse_config(args.config)

        # The active app, if defined.
        self.app = args.app or self.config.get('DEFAULT', 'default.app')

        # Load config fom a specific app, if defined.
        if self.app:
            self.config_section = 'app:%s' % self.app
        else:
            self.config_section = 'DEFAULT'

        # Prepend configured paths to sys.path, if any.
        sys.path[:0] = self.config.getlist(self.config_section, 'sys.path', [])

        if args.action not in self.actions:
            # Unknown action or --help.
            return self.parser.print_help()

        if args.help:
            # Delegate help to action.
            extras.append('--help')

        self.actions[args.action](self, extras)

    def parse_config(self, config_file):
        """Load configuration. If files are not specified, try 'tipfy.cfg'
        in the current dir.
        """
        self.config = Config()
        self.config_files = self.config.read([
            os.path.join(os.path.expanduser('~'), GLOBAL_CONFIG_FILE),
            os.path.abspath(config_file)
        ])


def main():
    manager = TipfyManager()
    manager(sys.argv[1:])


if __name__ == '__main__':
    main()
