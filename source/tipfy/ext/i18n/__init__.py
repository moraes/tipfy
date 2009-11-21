# -*- coding: utf-8 -*-
"""
    tipfy.ext.i18n
    ~~~~~~~~~~~~~~

    Internationalization extension.

    It requires the babel module to be added to the lib dir. Babel can be
    downloaded at http://babel.edgewall.org/

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import logging
from datetime import tzinfo, timedelta

from google.appengine.api import urlfetch

from babel.support import Translations, LazyProxy
from babel.dates import format_date as babel_format_date, \
    format_datetime as babel_format_datetime, format_time as babel_format_time

from tipfy import local, app, request, response

# Set proxy for the current locale code and translations object.
local.locale = local.translations = None
locale = local('locale')
translations = local('translations')

# Cache loaded translations and timezones.
_translations = {}
_timezones = {}


class I18nMiddleware(object):
    """Middleware to initialize internationalization on every request."""
    locale = None

    def process_request(self, request):
        # Get locale from a 'lang' query parameter, and if not set try to get
        # from a cookie. As last option, use the locale set in config.
        self.locale = request.args.get('lang', request.cookies.get(
            'tipfy.locale', app.config.locale))

        set_locale(self.locale)
        return None

    def process_response(self, request, response):
        if self.locale and self.locale != app.config.locale:
            # Persist locale using a cookie when it differs from default.
            response.set_cookie('tipfy.locale', value=self.locale,
                max_age=(86400 * 30))

        return response


def set_locale(locale):
    """Sets translations for the current request."""
    if locale not in _translations:
        options = list(set([locale, app.config.locale]))
        _translations[locale] = Translations.load('locale', options, 'messages')

    local.locale = locale
    local.translations = _translations[locale]


def fetch_jsontime_timezone(tz_name):
    """Fetches timezone info from a json-time service and returns a tzinfo
    object. By default it uses the service provided by
    `http://json-time.appspot.com/`_.

    This function derives from http://github.com/caio/bizarrice

    :param tz_name:
        A valid timezone name according to the Olson database. For example,
        'America/Chicago'.
    :return:
        A ``datetime.tzinfo`` object. If the timezone is not valid, tzinfo for
        UTC is returned.
    """
    url = getattr(local.app.config, 'json_time_service_url',
        'http://json-time.appspot.com/time.json')

    tz = _tzinfo_utc
    result = urlfetch.fetch('%s?tz=%s' % (url, tz_name))

    if result.status_code != 200:
        logging.error('Service JsonTime returned unexpected status code: %d'
                      % result.status_code)
    else:
        from django.utils import simplejson
        try:
            json = simplejson.loads(result.content)
        except ValueError:
            logging.error('Service JsonTime returned non-json content')
        else:
            if json['error']:
                logging.error('Invalid timezone "%s". Falling back to UTC.' %
                    timezone)
            else:
                # Returned date format is 'Fri, 20 Nov 2009 06:43:17 -0600'
                # First, extract the offset '-600'
                offset = json['datetime'].rsplit(' ', 1)[1]

                # Convert the offset to seconds
                # '-0600' is converted to ((6 * 3600) + (0 * 60)) * -1
                tz_offset = (int(offset[1:3]) * 3600) + (int(offset[3:]) * 60)
                if offset[0] == '-':
                    tz_offset *= -1

                tz = TimezoneOffset(tz_name, tz_offset)

    return tz


# Some functions borrowed from Zine: http://zine.pocoo.org/.
def gettext(string):
    """Translates a given string according to the current locale.

    :param string:
        The string to be translated.
    :return:
        The translated string.
    """
    return unicode(local.translations.gettext(string), 'utf-8')


def ngettext(singular, plural, n):
    """Translates a possible pluralized string  according to the current locale.

    :param singular:
        The singular for of the string to be translated.
    :param plural:
        The plural for of the string to be translated.
    :return:
        The translated string.
    """
    return unicode(local.translations.ngettext(singular, plural, n), 'utf-8')


def lazy_gettext(string):
    """A lazy version of :func:`gettext`.

    :param string:
        The string to be translated.
    :return:
        The translated string.
    """
    return LazyProxy(gettext, string)


def lazy_ngettext(singular, plural, n):
    """A lazy version of :func:`ngettext`.

    :param singular:
        The singular for of the string to be translated.
    :param plural:
        The plural for of the string to be translated.
    :return:
        The translated string.
    """
    return LazyProxy(ngettext, singular, plural, n)


def format_date(value=None, format='medium'):
    """Formats a ``datetime.date`` object according to the current locale.

    :param value:
        A datetime object.
    :param format:
        The format to be returned. Valid values are 'short', 'medium', 'long'
        and 'full'. Examples:

          - short:  11/10/09
          - medium: Nov 10, 2009
          - long:   November 10, 2009
          - full:   Tuesday, November 10, 2009

    :return:
        A formatted date string.
    """
    return babel_format_date(date=value, format=format, locale=local.locale)


def format_datetime(value=None, format='medium'):
    """Formats a ``datetime.datetime`` object according to the current locale.

    :param value:
        A datetime object.
    :param format:
        The format to be returned. Valid values are 'short', 'medium', 'long'
        and 'full'. Examples:

          - short:  11/10/09 4:36 PM
          - medium: Nov 10, 2009 4:36:05 PM
          - long:   November 10, 2009 4:36:05 PM +0000
          - full:   Tuesday, November 10, 2009 4:36:05 PM World (GMT) Time

    :return:
        A formatted datetime string.
    """
    return babel_format_datetime(datetime=value, format=format, tzinfo=tzinfo,
        locale=local.locale)


def format_time(value=None, format='medium'):
    """Formats a ``datetime.time`` object according to the current locale.

    :param value:
        A datetime object.
    :param format:
        The format to be returned. Valid values are 'short', 'medium', 'long'
        and 'full'. Examples:

          - short:  4:36 PM
          - medium: 4:36:05 PM
          - long:   4:36:05 PM +0000
          - full:   4:36:05 PM World (GMT) Time

    :return:
        A formatted time string.
    """
    return babel_format_time(time=value, format=format, tzinfo=local.tzinfo,
        locale=local.locale)


class TimezoneOffset(tzinfo):
    """
    This class derives from http://pypi.python.org/pypi/python-dateutil
    """
    ZERO = timedelta(0)

    def __init__(self, name, offset):
        self._name = name
        if offset == 0:
            self._offset = self.ZERO
        else:
            self._offset = timedelta(seconds=offset)

    def utcoffset(self, dt):
        return self._offset

    def dst(self, dt):
        return self.ZERO

    def tzname(self, dt):
        return self._name

    def __eq__(self, other):
        return (isinstance(other, TimezoneOffset) and
                self._offset == other._offset)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "%s('%s', %s)" % (self.__class__.__name__,
            self._name, self._offset.days * 86400 + self._offset.seconds)

    __reduce__ = object.__reduce__


# Default timezone object.
_tzinfo_utc = TimezoneOffset('UTC', 0)
# Alias to gettext.
_ = gettext
