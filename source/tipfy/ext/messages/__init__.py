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

from tipfy import local
try:
    from tipfy.ext.i18n import _
except ImportError:
    _ = unicode


class MessagesMiddleware(object):
    def process_request(self, request):
        """Adds messages attribute to the request and initializes the messages
        container.
        """
        request.messages = self

        # Set the messages container.
        self.messages = []

        # Check for flashes on each request.
        flash = get_flash()
        if flash:
            self.messages.append(flash)

        return None

    def __len__(self):
        return len(self.messages)

    def __unicode__(self):
        return unicode('\n'.join(unicode(msg) for msg in self.messages))

    def __str__(self):
        return self.__unicode__()

    def add(self, level, body, title=None, life=None):
        """Adds a status message.

        :param level: Message level. Common values are "info", "alert", "error"
            and "success".
        :param body: Message contents.
        :param title: Optional message title.
        :life: message duration in milliseconds. User interface can implement
            a mechanism to make the message disappear after this time. If not
            set, the message is permanent.
        """
        self.messages.append({
            'level': level,
            'title': title,
            'body':  body,
            'life':  life
        })

    def add_form_error(self, body=None, title=None):
        """Adds a form error message."""
        if body is None:
            body = _('A problem occurred. Please correct the errors listed in '
                'the form.')

        if title is None:
            title = _('Error')

        self.add('error', body, title=title, life=None)

    def set_flash(self, level, body, title=None, life=None):
        """Sets a flash message."""
        set_flash({
            'level': level,
            'title': title,
            'body':  body,
            'life':  life
        })


def get_flash(key='tipfy.flash'):
    """Reads and deletes a flash message. Flash messages are stored in a cookie
    and automatically deleted when read.
    """
    if key in local.request.cookies:
        data = simplejson.loads(b64decode(local.request.cookies[key]))
        local.response.delete_cookie(key)
        return data


def set_flash(data, key='tipfy.flash'):
    """Sets a flash message. Flash messages are stored in a cookie
    and automatically deleted when read.
    """
    local.response.set_cookie(key, value=b64encode(simplejson.dumps(data)))
