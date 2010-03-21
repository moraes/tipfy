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

from tipfy import cached_property, get_config, local
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
        local.ext_messages_delete = key
        return simplejson.loads(b64decode(local.request.cookies[key]))


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

    local.ext_messages_set = (key, data)


class FlashMiddleware(object):
    """:class:`tipfy.RequestHandler` middleware to start and persist flash
    messages.
    """
    def post_dispatch(self, handler, response):
        to_delete = getattr(local, 'ext_messages_delete', None)
        to_set = getattr(local, 'ext_messages_set', None)

        if to_delete and (not to_set or to_set[0] != to_delete):
            response.delete_cookie(to_delete)

        if to_set:
            data = b64encode(simplejson.dumps(to_set[1]))
            response.set_cookie(to_set[0], value=data)

        return response


class MessagesMixin(object):
    """:class:`tipfy.RequestHandler` mixin for system messages."""
    @property
    def messages(self):
        if getattr(self, '__ext_messages', None) is None:
            self.__ext_messages = []
            # Check for flashes on first access.
            flash = get_flash()
            if flash:
                self.__ext_messages.append(flash)

        return self.__ext_messages

    def set_message(self, level, body, title=None, life=5000):
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

    def set_form_error(self, body=None, title=None):
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

        self.set_message('error', body, title=title, life=None)

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
            'life':  life,
        })
