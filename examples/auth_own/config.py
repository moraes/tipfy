config = {}

config['tipfy'] = {
    'middleware': [
        # Enable debugger. It will be loaded only in development.
        'tipfy.ext.debugger.DebuggerMiddleware',
    ],
    'apps_installed': [
         'apps.users',
     ],
}

config['tipfy.ext.session'] = {
    # Change this!!!
    'secret_key': 'change_me',
}

config['tipfy.ext.auth'] = {
    'auth_system': 'tipfy.ext.auth.MultiAuth',
}
