# -*- coding: utf-8 -*-
"""
    tipfy.ext.messages
    ~~~~~~~~~~~~~~~~~~

    Simple messages extension. Provides an unified container for application
    status messages such as form results, flashes, alerts and so on.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from base64 import b64encode, b64decode
from django.utils import simplejson

from tipfy import local, get_config
from tipfy.ext.i18n import _

#: Default configuration values for this module. Keys are:
#:   - ``cookie_name``: The name of the cookie to store flash messages. Default
#:     is `tipfy.flash`.
default_config = {
    'cookie_name': 'tipfy.flash',
}

# Proxies to the messages variables set on each request.
local.messages = None
messages = local('messages')


def set_messages(request=None, app=None):
    """Application hook executed right before the handler is dispatched.

    It initializes the messages system.

    To enable it, add a hook to the list of hooks in ``config.py``:

    .. code-block:: python

       config = {
           'tipfy': {
               'hooks': {
                   'pre_dispatch_handler': ['tipfy.ext.messages:set_messages'],
                   # ...
               },
           },
       }

    :param request:
        A ``werkzeug.Request`` instance.
    :param app:
        A :class:`tipfy.WSGIApplication` instance.
    :return:
        ``None``.
    """
    local.messages = Messages()


class Messages(object):
    def __init__(self):
        """Initializes the messages container, loading a possibly existing
        flash message.
        """
        # Set the messages container.
        self.messages = []

        # Check for flashes on each request.
        flash = get_flash()
        if flash:
            self.messages.append(flash)

    def __len__(self):
        return len(self.messages)

    def __unicode__(self):
        return unicode('\n'.join(unicode(sorted(msg.items())) for msg in
            self.messages))

    def __str__(self):
        return self.__unicode__()

    def add(self, level, body, title=None, life=5000):
        """Adds a status message.

        :param level:
            Message level. Common values are "info", "alert", "error"
            and "success".
        :param body:
            Message contents.
        :param title:
            Optional message title.
        :life:
            Message life time in milliseconds. User interface can implement
            a mechanism to make the message disappear after the elapsed time.
            If not set, the message is permanent.
        :return:
            ``None``.
        """
        self.messages.append({
            'level': level,
            'title': title,
            'body':  body,
            'life':  life
        })

    def add_form_error(self, body=None, title=None):
        """Adds a form error message.

        :param body:
            Message contents.
        :param title:
            Optional message title.
        :return:
            ``None``.
        """
        if body is None:
            body = _('A problem occurred. Please correct the errors listed in '
                'the form.')

        if title is None:
            title = _('Error')

        self.add('error', body, title=title, life=None)

    def set_flash(self, level, body, title=None, life=5000):
        """Sets a flash message.

        :param level:
            Message level. Common values are "info", "alert", "error"
            and "success".
        :param body:
            Message contents.
        :param title:
            Optional message title.
        :life:
            Message life time in milliseconds. User interface can implement
            a mechanism to make the message disappear after the elapsed time.
            If not set, the message is permanent.
        :return:
            ``None``.
        """
        set_flash({
            'level': level,
            'title': title,
            'body':  body,
            'life':  life
        })


def get_flash():
    """Reads and deletes a flash message. Flash messages are stored in a cookie
    and automatically deleted when read.

    :return:
        The data stored in a flash, in any.
    """
    key = get_config(__name__, 'cookie_name')
    if key in local.request.cookies:
        data = simplejson.loads(b64decode(local.request.cookies[key]))
        local.response.delete_cookie(key)
        return data


def set_flash(data):
    """Sets a flash message. Flash messages are stored in a cookie
    and automatically deleted when read.

    :param data:
        Flash data to be serialized and stored as JSON.
    :return:
        ``None``.
    """
    key = get_config(__name__, 'cookie_name')
    local.response.set_cookie(key, value=b64encode(simplejson.dumps(data)))
