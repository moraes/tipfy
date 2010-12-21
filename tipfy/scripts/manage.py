#!/usr/bin/env python
import ConfigParser
import os
import runpy
import shutil
import re
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


def get_unique_sequence(seq):
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]


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


class Config(ConfigParser.RawConfigParser):
    """Wraps RawConfigParser `get*()` functions to allow a default to be
    returned instead of throwing errors. Also adds `getlist()` to split
    multi-line values into a list.
    """
    _interpolate_re = re.compile(r"%\(([^)]*)\)s")

    _boolean_states = {
        '1':     True,
        'yes':   True,
        'true':  True,
        'on':    True,
        '0':     False,
        'no':    False,
        'false': False,
        'off':   False,
    }

    def get(self, section, option, default=None, raw=False):
        return self._get_wrapper(section, option, unicode, default, raw)

    def getboolean(self, section, option, default=None, raw=False):
        return self._get_wrapper(section, option, self._to_boolean, default,
            raw)

    def getfloat(self, section, option, default=None, raw=False):
        return self._get_wrapper(section, option, self._to_float, default, raw)

    def getint(self, section, option, default=None, raw=False):
        return self._get_wrapper(section, option, self._to_int, default, raw)

    def getlist(self, section, option, default=None, raw=False, unique=True):
        res = self._get_wrapper(section, option, self._to_list, default, raw)
        if unique:
            return get_unique_sequence(res)

        return res

    def _get(self, section, option):
        return ConfigParser.RawConfigParser.get(self, section, option)

    def _to_boolean(self, value):
        key = value.lower()
        if key not in self._boolean_states:
            raise ValueError('Not a boolean: %r. Booleans must be '
                'one of %s.' % (value, ', '.join(self._boolean_states.keys())))

        return self._boolean_states[key]

    def _to_float(self, value):
        return float(value)

    def _to_int(self, value):
        return int(value)

    def _to_list(self, value):
        value = [line.strip() for line in value.splitlines()]
        return [v for v in value if v]

    def _get_wrapper(self, sections, option, converter, default, raw):
        """Wraps get functions allowing default values and a list of sections
        looked up in order until a value is found.
        """
        if isinstance(sections, basestring):
            sections = [sections]

        for section in sections:
            try:
                value = self._get(section, option)
                if not raw:
                    value = self._interpolate(section, option, value)

                return converter(value)
            except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                pass
            except ValueError:
                # Failed conversion?
                pass

        return default

    def _interpolate(self, section, option, value, tried=None):
        if not '%(' in value:
            return value

        matches = self._interpolate_re.findall(value)
        if not matches:
            return value

        if tried is None:
            tried = [(section, option)]

        variables = {}
        matches = get_unique_sequence(matches)
        for match in matches:
            parts = tuple(match.split('|', 1))
            if len(parts) == 1:
                new_section, new_option = section, match
            else:
                new_section, new_option = parts

            if parts in tried:
                continue

            tried.append(parts)
            try:
                found = self._get(new_section, new_option)
                tried.append(('DEFAULT', new_option))
                variables[match] = self._interpolate(new_section, new_option,
                    found, tried)
            except Exception:
                pass

        if len(matches) == len(variables):
            return value % variables

        raise ConfigParser.InterpolationError(section, option,
            'Cound not replace %r.' % value)


class Action(object):
    """Base interface for custom actions."""
    #: Action name.
    name = None

    #: ArgumentParser description.
    description = None

    #: ArgumentParser epilog.
    epilog = None

    def __init__(self, name):
        self.name = name

    def __call__(self, manager, argv):
        raise NotImplementedError()

    def get_config_section(self, manager):
        sections = ['tipfy:%s' % self.name]
        if manager.app:
            sections.insert(0, '%s:%s' % (manager.app, self.name))

        return sections

    def error(self, message, status=1):
        """Displays an error message and exits."""
        self.log(message)
        sys.exit(status)

    def log(self, message):
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

    def get_parser(self):
        parser = argparse.ArgumentParser(description=self.description)
        parser.add_argument('app_dir', help='App directory '
            'or directories.', nargs='+')
        parser.add_argument('-t', '--template', dest='template',
            help='App template, copied to the new project directory. '
            'If not defined, the default app skeleton is used.')
        return parser

    def __call__(self, manager, argv):
        section = self.get_config_section(manager)
        parser = self.get_parser()
        args = parser.parse_args(args=argv)

        template_dir = args.template
        if not template_dir:
            # Try getting the template set in config.
            template_dir = manager.config.get(section, 'appengine_stub')

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

    def create_app(self, manager, app_dir, template_dir):
        if os.path.exists(app_dir):
            self.error('Project directory already exists: %r.' % app_dir)

        shutil.copytree(template_dir, app_dir)


class GaeSdkAction(Action):
    """This is just a wrapper for tools found in the Google App Engine SDK.
    It delegates all arguments to the SDK script and no additional arguments
    are parsed.
    """
    def __call__(self, manager, argv):
        sys.argv = [self.name] + argv
        try:
            runpy.run_module(self.name, run_name='__main__', alter_sys=True)
        except ImportError:
            self.error(MISSING_GAE_SDK_MSG % dict(script=self.name))


class GaeSdkExtendedAction(Action):
    """Base class for actions that wrap the App Engine SDK scripts to make
    them configurable or to add before/after hooks. It accepts all options
    from the correspondent SDK scripts, but they can be configured in
    tipfy.cfg.
    """
    options = []

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
        section = self.get_config_section(manager)

        usage = '%%(prog)s %(action)s [--config CONFIG] [--app APP] ' \
            '[options]' % dict(action=self.name)

        parser = argparse.ArgumentParser(
            description=self.description,
            usage=usage,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False
        )

        for long_option, short_option, is_bool in self.get_getopt_options():
            args = ['--%s' % long_option]
            kwargs = {}

            if short_option:
                args.append('-%s' % short_option)

            if is_bool:
                kwargs['action'] = 'store_true'
                kwargs['default'] = manager.config.getboolean(section,
                    long_option)
            else:
                kwargs['default'] = manager.config.get(section, long_option)

            parser.add_argument(*args, **kwargs)

        # Add app path.
        app_path = manager.config.get(section, 'path', '')
        parser.add_argument('app', nargs='?', default=app_path)

        return parser

    def get_gae_argv(self, manager, argv):
        parser = self.get_parser_from_getopt_options(manager)
        args, extras = parser.parse_known_args(args=argv)

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

    Default values for each option can be defined in tipfy.cfg in the
    "tipfy:runserver" section or for the current app, sufixed by ":runserver".
    A special variable "app" is replaced by the value from the "--app"
    argument:

        [tipfy]
        path = /path/to/%(app)s

        [tipfy:runserver]
        debug = true
        datastore_path = /path/to/%(app)s.datastore

        [my_app:runserver]
        port = 8081

    In this case, executing:

        tipfy runserver --app=my_app

    ...will expand to:

        dev_appserver --datastore_path=/path/to/my_app.datastore --debug --port=8081 /path/to/my_app

    Define in "before" and "after" a list of functions to run before and after
    the server executes. These functions are imported so they must be in
    sys.path. For example:

        [tipfy:runserver]
        before =
            hooks.before_runserver_1
            hooks.before_runserver_2

        after =
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

    def get_base_gae_argv(self):
        return ['dev_appserver']

    def __call__(self, manager, argv):
        section = self.get_config_section(manager)
        before_hooks = manager.config.getlist(section, 'before', [])
        after_hooks = manager.config.getlist(section, 'after', [])

        # Assemble arguments.
        sys.argv = self.get_gae_argv(manager, argv)

        # Execute before scripts.
        self.run_hooks(before_hooks, manager, argv)

        script = 'dev_appserver'
        try:
            self.log('Executing: %s' % ' '.join(sys.argv))
            runpy.run_module(script, run_name='__main__', alter_sys=True)
        except ImportError:
            self.error(MISSING_GAE_SDK_MSG % dict(script=script))
        finally:
            # Execute after scripts.
            self.run_hooks(after_hooks, manager, argv)


class GaeDeployAction(GaeSdkExtendedAction):
    """
    A convenient wrapper for "appcfg update": deploys to Google App Engine
    using before and after hooks and allowing configurable defaults.

    Default values for each option can be defined in tipfy.cfg in the
    "tipfy:deploy" section or for the current app, sufixed by ":deploy".
    A special variable "app" is replaced by the value from the "--app"
    argument:

        [tipfy]
        path = /path/to/%(app)s

        [tipfy:deploy]
        verbose = true

        [my_app:deploy]
        email = user@gmail.com
        no_cookies = true

    In this case, executing:

        tipfy deploy --app=my_app

    ...will expand to:

        appcfg update --verbose --email=user@gmail.com --no_cookies /path/to/my_app

    Define in "before" and "after" a list of functions to run before and after
    deployment. These functions are imported so they must be in sys.path.
    For example:

        [tipfy:deploy]
        before =
            hooks.before_deploy_1
            hooks.before_deploy_2

        after =
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

    def get_base_gae_argv(self):
        return ['appcfg', 'update']

    def __call__(self, manager, argv):
        section = self.get_config_section(manager)
        before_hooks = manager.config.getlist(section, 'before', [])
        after_hooks = manager.config.getlist(section, 'after', [])

        # Assemble arguments.
        sys.argv = self.get_gae_argv(manager, argv)

        # Execute before scripts.
        self.run_hooks(before_hooks, manager, argv)

        script = 'appcfg'
        try:
            self.log('Executing: %s' % ' '.join(sys.argv))
            runpy.run_module(script, run_name='__main__', alter_sys=True)
        except ImportError:
            self.error(MISSING_GAE_SDK_MSG % dict(script=script))
        finally:
            # Execute after scripts.
            self.run_hooks(after_hooks, manager, argv)


class BuildAction(Action):
    description = 'Installs packages in the app directory.'

    def get_parser(self):
        # XXX cache option
        # XXX symlinks option
        parser = argparse.ArgumentParser(description=self.description)
        parser.add_argument('packages', help='Package names', nargs='+')
        parser.add_argument('app_dir', help='App directory.')
        return parser

    def __call__(self, manager, argv):
        parser = self.get_parser()
        args = parser.parse_args(args=argv)


class InstallAppengineSdkAction(Action):
    """Not implemented yet."""
    description = 'Downloads and unzips the App Engine SDK.'

    def get_parser(self):
        parser = argparse.ArgumentParser(description=self.description)
        parser.add_argument('--version', '-v', help='SDK version. '
            'If not defined, downloads the latest stable one.')
        return parser

    def __call__(self, manager, argv):
        parser = self.get_parser()
        raise NotImplementedError()


class TestAction(Action):
    """Testing stuff."""
    def __call__(self, manager, argv):
        print manager.app


class TipfyManager(object):
    description = 'Tipfy Management Utilities.'
    epilog = 'Use "%(prog)s action --help" for help on specific actions.'

    # XXX Allow users to hook in custom actions.
    default_actions = [
        # Wrappers for App Engine SDK tools.
        GaeSdkAction('appcfg'),
        GaeSdkAction('bulkload_client'),
        GaeSdkAction('bulkloader'),
        GaeSdkAction('dev_appserver'),
        GaeSdkAction('remote_api_shell'),
        # For now these are App Engine specific.
        GaeRunserverAction('runserver'),
        GaeDeployAction('deploy'),
        # Extra ones.
        # InstallAppengineSdkAction('install_gae_sdk'),
        CreateAppAction('create_app'),
        BuildAction('build'),
        TestAction('test'),
    ]

    def __init__(self):
        self.actions = dict((a.name, a) for a in self.default_actions)

    def __call__(self, argv):
        parser = self.get_parser()
        args, extras = parser.parse_known_args(args=argv)

        # Load configuration.
        self.parse_config(args.config)

        # Load config fom a specific app, if defined, or use default one.
        self.app = args.app or self.config.get('tipfy', 'app')

        # Fallback to the tipfy section.
        self.config_section = ['tipfy']
        if self.app:
            self.config_section.insert(0, self.app)

        # If app is set, an 'app' value can be used in expansions.
        if self.app:
            self.config.set('DEFAULT', 'app', self.app)

        # Prepend configured paths to sys.path, if any.
        sys.path[:0] = self.config.getlist(self.config_section, 'sys.path', [])

        if args.action not in self.actions:
            # Unknown action or --help.
            return parser.print_help()

        if args.help:
            # Delegate help to action.
            extras.append('--help')

        self.actions[args.action](self, extras)

    def get_parser(self):
        actions = ', '.join(sorted(self.actions.keys()))
        parser = argparse.ArgumentParser(description=self.description,
            epilog=self.epilog, add_help=False)
        parser.add_argument('action', help='Action to perform. '
            'Available actions are: %s.' % actions, nargs='?')
        parser.add_argument('--config', default='tipfy.cfg',
            help='Configuration file. If not provided, uses tipfy.cfg from '
            'the current directory.')
        parser.add_argument('--app', help='App configuration to load.')
        parser.add_argument('-h', '--help', help='Show this help message '
            'and exit.', action='store_true')
        return parser

    def parse_config(self, config_file):
        """Load configuration. If files are not specified, try 'tipfy.cfg'
        in the current dir.
        """
        self.config_files = {
            'global': os.path.realpath(os.path.join(os.path.expanduser('~'),
                GLOBAL_CONFIG_FILE)),
            'project': os.path.realpath(os.path.abspath(config_file)),
        }

        self.config = Config()
        self.config_loaded = self.config.read([
            self.config_files['global'],
            self.config_files['project'],
        ])


def main():
    manager = TipfyManager()
    manager(sys.argv[1:])


if __name__ == '__main__':
    main()
