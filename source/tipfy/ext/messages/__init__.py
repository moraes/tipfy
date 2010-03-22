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
        local.ext_messages_delete = getattr(local, 'ext_messages_delete', [])
        if key not in local.ext_messages_delete:
            local.ext_messages_delete.append(key)
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

    local.ext_messages_set = getattr(local, 'ext_messages_set', [])
    local.ext_messages_set.append((key, data))


class FlashMiddleware(object):
    """A :class:`tipfy.RequestHandler` middleware to set and delete flash
    messages.
    """
    def post_dispatch(self, handler, response):
        """Executes after a :class:`tipfy.RequestHandler` is dispatched. It
        must always return a response object, be it the one passed in the
        arguments or a new one.

        :param handler:
            A :class:`tipfy.RequestHandler` instance.
        :param response:
            A ``werkzeug.Response`` instance.
        :return:
            A ``werkzeug.Response`` instance.
        """
        to_set = getattr(local, 'ext_messages_set', [])
        to_delete = getattr(local, 'ext_messages_delete', [])

        if to_set or to_delete:
            keys = []
            for key, data in reversed(to_set):
                # Only set a same key once.
                if key not in keys:
                    keys.append(key)
                    response.set_cookie(key, b64encode(simplejson.dumps(data)))

            for key in to_delete:
                # Don't delete keys that were just set.
                if key not in keys:
                    response.delete_cookie(key)

            local.ext_messages_set = []
            local.ext_messages_delete = []

        return response


class MessagesMixin(object):
    """A :class:`tipfy.RequestHandler` mixin for system messages."""
    @cached_property
    def messages(self):
        if getattr(self, '_MessagesMixin__messages', None) is None:
            # Initialize messages list and check for flashes on first access.
            self.__messages = []
            flash = get_flash()
            if flash:
                self.__messages.append(flash)

        return self.__messages

    def set_message(self, level, body, title=None, life=5000, flash=False):
        """Adds a status message.

        :param level:
            Message level. Common values are "success", "error", "info" or
            "alert".
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
        message = {'level': level, 'title': title, 'body': body, 'life': life}
        if flash is True:
            set_flash(message)
        else:
            self.messages.append(message)

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

    def get_flash(self, key=None):
        """Returns a flash message, if set.

        :param key:
            Cookie name. If not provided, uses the default cookie value for
            flashes.
        :return:
            The data stored in a flash, in any.
        """
        return get_flash(key)

    def set_flash(self, data, key=None):
        """Sets a flash message.

        :param data:
            Flash data to be serialized and stored as JSON.
        :param key:
            Cookie name. If not provided, uses the default cookie value for
            flashes.
        :return:
            ``None``.
        """
        set_flash(data, key)
