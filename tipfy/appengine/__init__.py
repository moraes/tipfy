import os

# App Engine flags.
SERVER_SOFTWARE = os.environ.get('SERVER_SOFTWARE', '')
#: The application ID as defined in *app.yaml*.
APPLICATION_ID = os.environ.get('APPLICATION_ID')
#: The deployed version ID. Always '1' when using the dev server.
CURRENT_VERSION_ID = os.environ.get('CURRENT_VERSION_ID', '1')
#: True if the app is using App Engine dev server, False otherwise.
DEV_APPSERVER = SERVER_SOFTWARE.startswith('Development')
#: True if the app is running on App Engine, False otherwise.
APPENGINE = (APPLICATION_ID is not None and (DEV_APPSERVER or
    SERVER_SOFTWARE.startswith('Google App Engine')))
