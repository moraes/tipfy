config = {}

config['tipfy'] = {
    'middleware': [
        # Enable debugger. It will be loaded only in development.
        'tipfy.ext.debugger.DebuggerMiddleware',
    ],
}

config['tipfy'] = {
    'apps_installed': [
         'apps.users',
     ],
}
