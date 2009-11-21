# -*- coding: utf-8 -*-
"""
    tipfy.ext.i18n
    ~~~~~~~~~~~~~~

    Internationalization extension.

    It requires the babel and gae-pytz modules to be added to the lib dir.

    Babel can be downloaded at http://babel.edgewall.org/

    gae-pytz can be downloaded at http://code.google.com/p/gae-pytz/

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from babel.support import Translations, LazyProxy
from babel.dates import format_date as _format_date, \
    format_datetime as _format_datetime, format_time as _format_time
from pytz.gae import pytz

from tipfy import local, app

# Set proxy for the current locale code and translations object.
local.locale = local.translations = None
locale = local('locale')
translations = local('translations')

# Cache loaded translations and timezones.
_translations = {}
_timezones = {}


class I18nMiddleware(object):
    """Middleware to initialize internationalization on every request.

    To enable it, add ``tipfy.ext.i18n.I18nMiddleware``  to the list of
    middleware classes in ``config.py``:

    .. code-block:: python

       middleware_classes = [
           'tipfy.ext.i18n.I18nMiddleware',
           # ...
       ]

    It must be placed before any other middleware that will make use of
    internationalization. Normally it is the first or one of the first
    middlewares to be set.
    """
    locale = None

    def process_request(self, request):
        # Get locale from a 'lang' query parameter, and if not set try to get
        # from a cookie. As last option, use the locale set in config.
        self.locale = request.args.get('lang', request.cookies.get(
            'tipfy.locale', app.config.locale))

        set_locale(self.locale)

    def process_response(self, request, response):
        if self.locale and self.locale != app.config.locale:
            # Persist locale using a cookie when it differs from default.
            response.set_cookie('tipfy.locale', value=self.locale,
                max_age=(86400 * 30))

        return response


def set_locale(locale):
    """Sets the locale and loads a translation for the current request, if not
    already loaded. This is called by :class:`I18nMiddleware` on each request.

    :param locale:
        The locale code. For example, 'en_US' or 'pt_BR'.
    :return:
        `None`.
    """
    if locale not in _translations:
        options = list(set([locale, app.config.locale]))
        _translations[locale] = Translations.load('locale', options, 'messages')

    local.locale = locale
    local.translations = _translations[locale]


def gettext(string):
    """Translates a given string according to the current locale.

    :param string:
        The string to be translated.
    :return:
        The translated string.
    """
    return unicode(local.translations.gettext(string), 'utf-8')


def ngettext(singular, plural, n):
    """Translates a possible pluralized string according to the current locale.

    :param singular:
        The singular for of the string to be translated.
    :param plural:
        The plural for of the string to be translated.
    :param n:
        An integer indicating if this is a singular or plural. If greater than
        1, it is a plural.
    :return:
        The translated string.
    """
    return unicode(local.translations.ngettext(singular, plural, n), 'utf-8')


def lazy_gettext(string):
    """A lazy version of :func:`gettext`.

    :param string:
        The string to be translated.
    :return:
        A ``LazyProxy`` object that when accessed translates the string.
    """
    return LazyProxy(gettext, string)


def lazy_ngettext(singular, plural, n):
    """A lazy version of :func:`ngettext`.

    :param singular:
        The singular for of the string to be translated.
    :param plural:
        The plural for of the string to be translated.
    :param n:
        An integer indicating if this is a singular or plural. If greater than
        1, it is a plural.
    :return:
        A ``LazyProxy`` object that when accessed translates the string.
    """
    return LazyProxy(ngettext, singular, plural, n)


def format_date(date=None, format='medium'):
    """Returns a date formatted according to the given pattern and following
    the current locale.

    :param date:
        A ``date`` or ``datetime`` object. If `None`, the current date in UTC
        is used.
    :param format:
        The format to be returned. Valid values are "short", "medium", "long",
        "full" or a custom date/time pattern. Example outputs:

          - short:  11/10/09
          - medium: Nov 10, 2009
          - long:   November 10, 2009
          - full:   Tuesday, November 10, 2009

    :return:
        A formatted date in unicode.
    """
    return _format_date(date=date, format=format, locale=local.locale)


def format_datetime(datetime=None, format='medium', timezone=None):
    """Returns a date and time formatted according to the given pattern and
    following the current locale and timezone.

    :param datetime:
        A ``datetime`` object. If `None`, the current date and time in UTC is
        used.
    :param format:
        The format to be returned. Valid values are "short", "medium", "long",
        "full" or a custom date/time pattern. Example outputs:

          - short:  11/10/09 4:36 PM
          - medium: Nov 10, 2009 4:36:05 PM
          - long:   November 10, 2009 4:36:05 PM +0000
          - full:   Tuesday, November 10, 2009 4:36:05 PM World (GMT) Time

    :param timezone:
        The timezone name from the Olson database. For example:
        'America/Chicago'. If not set, uses the default set in config, or UTC..
    :return:
        A formatted date and time in unicode.
    """
    return _format_datetime(datetime=datetime, format=format,
        tzinfo=get_tzinfo(timezone), locale=local.locale)


def format_time(time=None, format='medium', timezone=None):
    """Returns a time formatted according to the given pattern and following
    the current locale and timezone.

    :param time:
        A ``time`` or ``datetime`` object. If `None`, the current time in UTC
        is used.
    :param format:
        The format to be returned. Valid values are "short", "medium", "long",
        "full" or a custom date/time pattern. Example outputs:

          - short:  4:36 PM
          - medium: 4:36:05 PM
          - long:   4:36:05 PM +0000
          - full:   4:36:05 PM World (GMT) Time

    :param timezone:
        The timezone name from the Olson database. For example:
        'America/Chicago'. If not set, uses the default set in config, or UTC..
    :return:
        A formatted time in unicode.
    """
    return _format_time(time=time, format=format, tzinfo=get_tzinfo(timezone),
        locale=local.locale)


def get_tzinfo(timezone=None):
    """Returns a ``datetime.tzinfo`` object for the given timezone. This is
    called by :func:`format_datetime` and :func:`format_time` when a tzinfo
    is not provided.

    :param timezone:
        The timezone name from the Olson database. For example:
        'America/Chicago'. If not set, uses the default set in config, or UTC.
    :return:
        A ``datetime.tzinfo`` object.
    """
    if timezone is None:
        timezone = getattr(app.config, 'timezone', 'UTC')

    if timezone not in _timezones:
        _timezones[timezone] = pytz.timezone(timezone)

    return _timezones[timezone]


def to_local_timezone(datetime, timezone=None):
    """Returns a datetime object converted to the local timezone.

    This function derives from `Kay`_.

    :param datetime:
        A ``datetime`` object.
    :param timezone:
        The timezone name from the Olson database. For example:
        'America/Chicago'. If not set, uses the default set in config, or UTC.
    :return:
        A ``datetime`` object normalized to a timezone.
    """
    tzinfo = get_tzinfo(timezone)
    if datetime.tzinfo is None:
        datetime = datetime.replace(tzinfo=pytz.UTC)

    return tzinfo.normalize(datetime.astimezone(tzinfo))


def to_utc(datetime, timezone=None):
    """Convert a datetime object to UTC and drop tzinfo.

    This function derives from `Kay`_.

    :param datetime:
        A ``datetime`` object.
    :param timezone:
        The timezone name from the Olson database. For example:
        'America/Chicago'. If not set, uses the default set in config, or UTC.
    :return:
        A naive ``datetime`` object (no timezone), converted to UTC.
    """
    if datetime.tzinfo is None:
        tzinfo = get_tzinfo(timezone)
        datetime = tzinfo.localize(datetime)

    return datetime.astimezone(pytz.UTC).replace(tzinfo=None)


# Common alias to gettext.
_ = gettext
