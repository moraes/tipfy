config = {}

config['tipfy'] = {
    'middleware': [
        # Enable debugger. It will be loaded only in development.
        'tipfy.ext.debugger.DebuggerMiddleware',
        # This middleware will handle exceptions for the whole application.
        'exception_handler.ExceptionMiddleware',
    ],
}
