#!/usr/bin/env python
HELP = """Runs a development application server for an application.

%(script)s [options] <application root>

Application root must be the path to the application to run in this server.
Must contain a valid app.yaml or app.yml file.

Options:
  --help, -h                 View this helpful message.
  --debug, -d                Use debug logging. (Default false)
  --clear_datastore, -c      Clear the Datastore on startup. (Default false)
  --address=ADDRESS, -a ADDRESS
                             Address to which this server should bind. (Default
                             %(address)s).
  --port=PORT, -p PORT       Port for the server to run on. (Default %(port)s)
  --blobstore_path=PATH      Path to use for storing Blobstore file stub data.
                             (Default %(blobstore_path)s)
  --datastore_path=PATH      Path to use for storing Datastore file stub data.
                             (Default %(datastore_path)s)
  --use_sqlite               Use the new, SQLite based datastore stub.
                             (Default false)
  --history_path=PATH        Path to use for storing Datastore history.
                             (Default %(history_path)s)
  --require_indexes          Disallows queries that require composite indexes
                             not defined in index.yaml.
  --smtp_host=HOSTNAME       SMTP host to send test mail to.  Leaving this
                             unset will disable SMTP mail sending.
                             (Default '%(smtp_host)s')
  --smtp_port=PORT           SMTP port to send test mail to.
                             (Default %(smtp_port)s)
  --smtp_user=USER           SMTP user to connect as.  Stub will only attempt
                             to login if this field is non-empty.
                             (Default '%(smtp_user)s').
  --smtp_password=PASSWORD   Password for SMTP server.
                             (Default '%(smtp_password)s')
  --enable_sendmail          Enable sendmail when SMTP not configured.
                             (Default false)
  --show_mail_body           Log the body of emails in mail stub.
                             (Default false)
  --auth_domain              Authorization domain that this app runs in.
                             (Default gmail.com)
  --debug_imports            Enables debug logging for module imports, showing
                             search paths used for finding modules and any
                             errors encountered during the import process.
  --allow_skipped_files      Allow access to files matched by app.yaml's
                             skipped_files (default False)
  --disable_static_caching   Never allow the browser to cache static files.
                             (Default enable if expiration set in app.yaml)
"""
import ConfigParser
import getopt
import os
import sys


ALL_OPTIONS = {
    '-h':                       'help',
    '--help':                   'help',
    '-d':                       'debug',
    '--debug':                  'debug',
    '-p':                       'port',
    '--port':                   'port',
    '-a':                       'address',
    '--address':                'address',
    '--blobstore_path':         'blobstore_path',
    '--datastore_path':         'datastore_path',
    '--use_sqlite':             'use_sqlite',
    '--history_path':           'history_path',
    '-c':                       'clear_datastore',
    '--clear_datastore':        'clear_datastore',
    '--require_indexes':        'require_indexes',
    '--smtp_host':              'smtp_host',
    '--smtp_port':              'smtp_port',
    '--smtp_user':              'smtp_user',
    '--smtp_password':          'smtp_password',
    '--enable_sendmail':        'enable_sendmail',
    '--show_mail_body':         'show_mail_body',
    '--auth_domain':            'auth_domain',
    '--debug_imports':          'debug_imports',
    '--template_dir':           'template_dir',
    '--admin_console_server':   'admin_console_server',
    '--admin_console_host':     'admin_console_host',
    '--allow_skipped_files':    'allow_skipped_files',
    '--disable_static_caching': 'disable_static_caching',
    '--trusted':                'trusted',
}

BOOLEAN_OPTIONS = [
    'help',
    'debug',
    'use_sqlite',
    'clear_datastore',
    'require_indexes',
    'enable_sendmail',
    'show_mail_body',
    'debug_imports',
    'allow_skipped_files',
    'disable_static_caching',
    'trusted',
]


def print_help_and_exit(defaults, code):
    try:
        from google.appengine.tools.dev_app_server_main import DEFAULT_ARGS
        values = DEFAULT_ARGS.copy()
    except ImportError, e:
        values = {
            'script':         '',
            'address':        'localhost',
            'port':           '8080',
            'datastore_path': 'not set',
            'blobstore_path': 'not set',
            'history_path':   'not set',
            'smtp_host':      '',
            'smtp_port':      '25',
            'smtp_user':      '',
            'smtp_password':  '',
        }

    values['script'] = os.path.basename(sys.argv[0])
    values.update(defaults)
    values['datastore_path'] = os.path.abspath(values['datastore_path'])
    values['blobstore_path'] = os.path.abspath(values['blobstore_path'])
    values['history_path']   = os.path.abspath(values['history_path'])

    print HELP % values
    sys.stdout.flush()
    sys.exit(code)


def get_config_section(config_file, name):
    try:
        config = ConfigParser.RawConfigParser()
        config.read(config_file)
        return config.items(name)
    except ConfigParser.NoSectionError:
        return []


def get_default_app_path(config_file):
    return dict(get_config_section(config_file, 'app')).get('path', None)


def get_default_dev_appserver_options(config_file):
    return get_config_section(config_file, 'dev_appserver')


def get_dev_appserver_options(argv, config_file):
    """Returns parsed options for the dev_app_server, applying project's
    defaults.
    """
    default_options = get_default_dev_appserver_options(config_file)

    try:
        opts, args = getopt.gnu_getopt(
            argv[1:],
            'a:cdhp:', [
                'address=',
                'admin_console_server=',
                'admin_console_host=',
                'allow_skipped_files',
                'auth_domain=',
                'clear_datastore',
                'blobstore_path=',
                'datastore_path=',
                'use_sqlite',
                'debug',
                'debug_imports',
                'enable_sendmail',
                'disable_static_caching',
                'show_mail_body',
                'help',
                'history_path=',
                'port=',
                'require_indexes',
                'smtp_host=',
                'smtp_password=',
                'smtp_port=',
                'smtp_user=',
                'template_dir=',
                'trusted',
            ]
        )
    except getopt.GetoptError, e:
        print >>sys.stderr, 'Error: %s' % e
        print_help_and_exit(default_options, 1)

    temp_options = []
    extra_options = []
    for option, value in opts:
        if option in ('-h', '--help'):
            print_help_and_exit(default_options, 0)

        if option not in ALL_OPTIONS:
            extra_options.append((option, value))
            continue

        temp_options.append((ALL_OPTIONS.get(option), value))

    if not args:
        # Use default app
        app_path = get_default_app_path(config_file)
        if app_path:
            args = [app_path]

    # Assemble new sys.argv.
    new_argv = []

    options = dict(default_options)
    options.update(temp_options)

    # Add recognized options.
    for name, value in options.iteritems():
        arg = '--%s' % name
        if name not in BOOLEAN_OPTIONS:
            arg += '=%s' % value

        new_argv.append(arg)

    # Add extra (unknown) options.
    for name, value in extra_options:
        arg = '--%s' % name
        if value:
            arg += '=%s' % value
        new_argv.append(arg)

    # Add the app path.
    new_argv.append(args[0])
    return new_argv
