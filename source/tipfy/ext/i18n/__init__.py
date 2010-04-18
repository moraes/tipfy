# -*- coding: utf-8 -*-
"""
    tipfy.ext.i18n
    ~~~~~~~~~~~~~~

    Internationalization extension.

    This module provides internationalization utilities: a translations store,
    hooks to set locale for the current request, functions to manipulate
    dates according to timezones or translate and localize strings and dates.

    Tipfy uses `Babel`_ to manage translations of strings and localization of
    dates and times, and `gae-pytz`_ to handle timezones.

    Babel can be downloaded at http://babel.edgewall.org/

    gae-pytz can be downloaded at http://code.google.com/p/gae-pytz/

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from babel.support import Translations, LazyProxy
from babel import dates, numbers
from pytz.gae import pytz

from tipfy import local, get_config, normalize_callable

#: Default configuration values for this module. Keys are:
#:
#: - ``locale``: The application default locale code. Default is ``en_US``.
#:
#: - ``timezone``: The application default timezone according to the Olson
#:   database. Default is ``America/Chicago``.
#:
#: - ``cookie_name``: Cookie name used to save requested locale, in case
#:   cookies are used.
#:
#: - ``locale_request_lookup``: A list of tuples ``(method, key)`` to search
#:   for the locale to be loaded for the current request. The methods are
#:   searched in order until a locale is found. Available methods are:
#:
#:   - ``args``: gets the locale code from ``GET`` arguments.
#:   - ``form``: gets the locale code from ``POST`` arguments.
#:   - ``cookies``: gets the locale code from a cookie.
#:   - ``rule_args``: gets the locale code from the keywords in the current
#:     URL rule.
#:
#:   If none of the methods find a locale code, uses the default locale.
#:
#:   Default is ``[('args', 'lang'), ('cookies', 'tipfy.locale')]``: gets the
#:   locale from a ``lang`` parameter set in ``GET``, and if not set tries to
#:   get it from a cookie named ``tipfy.locale``.
default_config = {
    'locale':   'en_US',
    'timezone': 'America/Chicago',
    'cookie_name': 'tipfy.locale',
    'locale_request_lookup': [('args', 'lang'), ('cookies', 'tipfy.locale')],
}

# Proxies to the i18n variables set on each request.
local.locale = local.translations = None
locale, translations = local('locale'), local('translations')

# Cache loaded translations and timezones.
_translations = {}
_timezones = {}


class I18nMiddleware(object):
    """:class:`tipfy.RequestHandler` middleware that saves the current locale
    in a cookie at the end of request, if it differs from the default locale.
    """
    def post_dispatch(self, handler, response):
        """Saves current locale in a cookie if it is different from the default.

        :param handler:
            The current :class:`tipfy.RequestHandler` instance.
        :param response:
            The current ``werkzeug.Response`` instance.
        """
        if getattr(local, 'locale', None) is None:
            # Locale isn't set.
            return response

        if not is_default_locale():
            # Persist locale using a cookie when it differs from default.
            response.set_cookie(get_config(__name__, 'cookie_name'),
                value=get_locale(), max_age=(86400 * 30))

        return response

    def pre_dispatch_handler(self):
        """Called if i18n is used as a WSGIApplication middleware."""
        set_translations_from_request()
        return None

    def post_dispatch_handler(self, response):
        """Called if i18n is used as a WSGIApplication middleware."""
        return self.post_dispatch(None, response)


def get_locale():
    """Returns the current locale code. Forces loading translations for the
    current request if it was not set already.

    :return:
        The current locale code, e.g., ``en_US``.
    """
    if getattr(local, 'locale', None) is None:
        try:
            # Set translations based on the current request.
            set_translations_from_request()
        except AttributeError, e:
            # Simply set translations using default locale.
            set_translations(get_config(__name__, 'locale'))

    return local.locale


def get_translations():
    """Returns the current translations object. Forces loading translations for
    the current request if it was not set already.

    :return:
        A ``babel.support.Translations`` object.
    """
    if getattr(local, 'translations', None) is None:
        try:
            # Set translations based on the current request.
            set_translations_from_request()
        except AttributeError, e:
            # Simply set translations using default locale.
            set_translations(get_config(__name__, 'locale'))

    return local.translations


def set_translations(locale):
    """Sets the locale and translations object for the current request. Most
    functions in this module depends on the translations object being set to
    work properly.

    :param locale:
        The locale code. For example, ``en_US`` or ``pt_BR``.
    :return:
        ``None``.
    """
    if locale not in _translations:
        options = list(set([locale, get_config(__name__, 'locale')]))
        _translations[locale] = Translations.load('locale', options, 'messages')

    local.locale = locale
    local.translations = _translations[locale]


def set_translations_from_request():
    """Sets a translations object for the current request.

    It will use the configuration for ``locale_request_lookup`` to search for
    a key in ``GET``, ``POST``, cookie or keywords in the current URL rule.
    The configuration defines the search order. If no locale is set in any of
    these, uses the default locale set in config.

    By default it gets the locale from a ``lang`` GET parameter, and if not set
    tries to get it from a cookie. This is represented by the default
    configuration value ``[('args', 'lang'), ('cookies', 'tipfy.locale')]``.

    :param app:
        The WSGI application instance.
    :param request:
        The ``werkzeug.Request`` instance.
    :return:
        ``None``.
    """
    locale = None
    request = local.request
    app = local.app
    for method, key in get_config(__name__, 'locale_request_lookup'):
        if method in ('args', 'form', 'cookies'):
            # Get locale from GET, POST or cookies.
            locale = getattr(request, method).get(key, None)
        elif method == 'rule_args':
            # Get locale from current URL rule keywords.
            locale = app.rule_args.get(key, None)

        if locale is not None:
            break
    else:
        locale = get_config(__name__, 'locale')

    set_translations(locale)


def is_default_locale():
    """Returns ``True`` if locale is set to the default locale.

    :return:
        ``True`` if locale is set to the default locale, ``False`` otherwise.
    """
    return getattr(local, 'locale', None) == get_config(__name__, 'locale')


def gettext(string):
    """Translates a given string according to the current locale.

    :param string:
        The string to be translated.
    :return:
        The translated string.
    """
    return unicode(get_translations().gettext(string), 'utf-8')


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
    return unicode(get_translations().ngettext(singular, plural, n), 'utf-8')


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
        A ``date`` or ``datetime`` object. If ``None``, the current date in UTC
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
    return dates.format_date(date=date, format=format, locale=get_locale())


def format_datetime(datetime=None, format='medium', timezone=None):
    """Returns a date and time formatted according to the given pattern and
    following the current locale and timezone.

    :param datetime:
        A ``datetime`` object. If ``None``, the current date and time in UTC is
        used.
    :param format:
        The format to be returned. Valid values are "short", "medium", "long",
        "full" or a custom date/time pattern. Example outputs:

          - short:  11/10/09 4:36 PM
          - medium: Nov 10, 2009 4:36:05 PM
          - long:   November 10, 2009 4:36:05 PM +0000
          - full:   Tuesday, November 10, 2009 4:36:05 PM World (GMT) Time

    :param timezone:
        The timezone name from the Olson database, e.g.: 'America/Chicago'.
        If not set, uses the default returned by :func:`get_tzinfo`.
    :return:
        A formatted date and time in unicode.
    """
    return dates.format_datetime(datetime=datetime, format=format,
        tzinfo=get_tzinfo(timezone), locale=get_locale())


def format_time(time=None, format='medium', timezone=None):
    """Returns a time formatted according to the given pattern and following
    the current locale and timezone.

    :param time:
        A ``time`` or ``datetime`` object. If ``None``, the current time in UTC
        is used.
    :param format:
        The format to be returned. Valid values are "short", "medium", "long",
        "full" or a custom date/time pattern. Example outputs:

          - short:  4:36 PM
          - medium: 4:36:05 PM
          - long:   4:36:05 PM +0000
          - full:   4:36:05 PM World (GMT) Time

    :param timezone:
        The timezone name from the Olson database, e.g.: 'America/Chicago'.
        If not set, uses the default returned by :func:`get_tzinfo`.
    :return:
        A formatted time in unicode.
    """
    return dates.format_time(time=time, format=format,
        tzinfo=get_tzinfo(timezone), locale=get_locale())


def get_tzinfo(timezone=None):
    """Returns a ``datetime.tzinfo`` object for the given timezone. This is
    called by :func:`format_datetime` and :func:`format_time` when a tzinfo
    is not provided.

    :param timezone:
        The timezone name from the Olson database, e.g.: 'America/Chicago'.
        If not set, uses the default configuration value.
    :return:
        A ``datetime.tzinfo`` object.
    """
    if timezone is None:
        timezone = get_config(__name__, 'timezone')

    if timezone not in _timezones:
        _timezones[timezone] = pytz.timezone(timezone)

    return _timezones[timezone]


def to_local_timezone(datetime, timezone=None):
    """Returns a datetime object converted to the local timezone.

    This function derives from `Kay`_.

    :param datetime:
        A ``datetime`` object.
    :param timezone:
        The timezone name from the Olson database, e.g.: 'America/Chicago'.
        If not set, uses the default returned by :func:`get_tzinfo`.
    :return:
        A ``datetime`` object normalized to a timezone.
    """
    tzinfo = get_tzinfo(timezone)
    if datetime.tzinfo is None:
        datetime = datetime.replace(tzinfo=pytz.UTC)

    return tzinfo.normalize(datetime.astimezone(tzinfo))


def to_utc(datetime, timezone=None):
    """Returns a datetime object converted to UTC and without tzinfo.

    This function derives from `Kay`_.

    :param datetime:
        A ``datetime`` object.
    :param timezone:
        The timezone name from the Olson database, e.g.: 'America/Chicago'.
        If not set, uses the default returned by :func:`get_tzinfo`.
    :return:
        A naive ``datetime`` object (no timezone), converted to UTC.
    """
    if datetime.tzinfo is None:
        tzinfo = get_tzinfo(timezone)
        datetime = tzinfo.localize(datetime)

    return datetime.astimezone(pytz.UTC).replace(tzinfo=None)


def format_number(number):
    """Returns the given number formatted for a specific locale.

    >>> format_number(1099, locale='en_US')
    u'1,099'

    :param number:
        The number to format.
    :return:
        The formatted number.
    """
    # Do we really need this one?
    return numbers.format_number(number, locale=get_locale())


def format_decimal(number, format=None):
    """Returns the given decimal number formatted for a specific locale.

    >>> format_decimal(1.2345, locale='en_US')
    u'1.234'
    >>> format_decimal(1.2346, locale='en_US')
    u'1.235'
    >>> format_decimal(-1.2346, locale='en_US')
    u'-1.235'
    >>> format_decimal(1.2345, locale='sv_SE')
    u'1,234'
    >>> format_decimal(12345, locale='de')
    u'12.345'

    The appropriate thousands grouping and the decimal separator are used for
    each locale:

    >>> format_decimal(12345.5, locale='en_US')
    u'12,345.5'

    :param number:
        The number to format.
    :param format:
    :return:
        The formatted decimal number.
    """
    return numbers.format_decimal(number, format=format, locale=get_locale())


def format_currency(number, currency, format=None):
    """Returns a formatted currency value.

    >>> format_currency(1099.98, 'USD', locale='en_US')
    u'$1,099.98'
    >>> format_currency(1099.98, 'USD', locale='es_CO')
    u'US$\\xa01.099,98'
    >>> format_currency(1099.98, 'EUR', locale='de_DE')
    u'1.099,98\\xa0\\u20ac'

    The pattern can also be specified explicitly:

    >>> format_currency(1099.98, 'EUR', u'\\xa4\\xa4 #,##0.00', locale='en_US')
    u'EUR 1,099.98'

    :param number:
        The number to format.
    :param currency:
        The currency code.
    :return:
        The formatted currency value.
    """
    return numbers.format_currency(number, currency, format=format,
        locale=get_locale())


def format_percent(number, format=None):
    """Return formatted percent value for a specific locale.

    >>> format_percent(0.34, locale='en_US')
    u'34%'
    >>> format_percent(25.1234, locale='en_US')
    u'2,512%'
    >>> format_percent(25.1234, locale='sv_SE')
    u'2\\xa0512\\xa0%'

    The format pattern can also be specified explicitly:

    >>> format_percent(25.1234, u'#,##0\u2030', locale='en_US')
    u'25,123\u2030'

    :param number:
        The percent number to format
    :param format:
    :return:
        The formatted percent number
    """
    return numbers.format_percent(number, format=format, locale=get_locale())


def format_scientific(number, format=None):
    """Return value formatted in scientific notation for a specific locale.

    >>> format_scientific(10000, locale='en_US')
    u'1E4'

    The format pattern can also be specified explicitly:

    >>> format_scientific(1234567, u'##0E00', locale='en_US')
    u'1.23E06'

    :param number:
        The number to format.
    :param format:
    :return:
        Value formatted in scientific notation.
    """
    return numbers.format_scientific(number, format=format, locale=get_locale())


def parse_number(string):
    """Parse localized number string into a long integer.

    >>> parse_number('1,099', locale='en_US')
    1099L
    >>> parse_number('1.099', locale='de_DE')
    1099L

    When the given string cannot be parsed, an exception is raised:

    >>> parse_number('1.099,98', locale='de')
    Traceback (most recent call last):
        ...
    NumberFormatError: '1.099,98' is not a valid number

    :param string:
        The string to parse.
    :return:
        The parsed number.
    :raise `NumberFormatError`:
        If the string can not be converted to a number
    """
    return numbers.parse_number(string, locale=get_locale())


def parse_decimal(string):
    """Parse localized decimal string into a float.

    >>> parse_decimal('1,099.98', locale='en_US')
    1099.98
    >>> parse_decimal('1.099,98', locale='de')
    1099.98

    When the given string cannot be parsed, an exception is raised:

    >>> parse_decimal('2,109,998', locale='de')
    Traceback (most recent call last):
        ...
    NumberFormatError: '2,109,998' is not a valid decimal number

    :param string:
        The string to parse.
    :return:
        The parsed decimal number.
    :raise `NumberFormatError`:
        If the string can not be converted to a decimal number
    """
    return numbers.parse_decimal(string, locale=get_locale())


# Common alias to gettext.
_ = gettext
# Old names, kept here for backwards compatibility.
set_locale = set_translations
set_requested_locale = set_translations_from_request
