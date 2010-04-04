config = {}

config['tipfy'] = {
    'middleware': [
        # Enable debugger. It will be loaded only in development.
        'tipfy.ext.debugger.DebuggerMiddleware',
        # Enable appstats.
        'tipfy.ext.appstats.AppstatsMiddleware',
    ],
}
