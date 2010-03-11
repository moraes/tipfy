# -*- coding: utf-8 -*-
"""
    tipfy.ext.messages
    ~~~~~~~~~~~~~~~~~~

    Simple messages extension. Provides an unified container for application
    status messages such as form results, flashes, alerts and so on.

    :copyright: 2010 by tipfy.org.
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


def get_flash(key=None):
    """Reads and deletes a flash message. Flash messages are stored in a cookie
    and automatically deleted when read.

    :param key:
        Cookie name. If not provided, uses the ``cookie_name`` value configured
        for this module.
    :return:
        The data stored in a flash, in any.
    """
    if key is None:
        key = get_config(__name__, 'cookie_name')

    if key in local.request.cookies:
        data = simplejson.loads(b64decode(local.request.cookies[key]))
        local.response.delete_cookie(key)
        return data


def set_flash(data, key=None):
    """Sets a flash message. Flash messages are stored in a cookie
    and automatically deleted when read.

    :param data:
        Flash data to be serialized and stored as JSON.
    :param key:
        Cookie name. If not provided, uses the ``cookie_name`` value configured
        for this module.
    :return:
        ``None``.
    """
    if key is None:
        key = get_config(__name__, 'cookie_name')

    local.response.set_cookie(key, value=b64encode(simplejson.dumps(data)))


def set_messages(key=None):
    """A decorator for :class:`tipfy.RequestHandler` methods. Sets a
    :class:`Messages` instance in the request handler as the attribute
    ``messages``.

    :param key:
        Cookie name. If not provided, uses the ``cookie_name`` value configured
        for this module.
    :return:
        ``None``.
    """
    def get_decorator(method):
        def decorator(self, *args, **kwargs):
            self.messages = Messages(key)
            return method(self, *args, **kwargs)

        return decorator
    return get_decorator


class Messages(object):
    def __init__(self, key=None):
        """Initializes the messages container, loading a possibly existing
        flash message.
        """
        # Set the messages container.
        self.key = key
        self.messages = []

        # Check for flashes on each request.
        flash = get_flash(self.key)
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
        }, self.key)
