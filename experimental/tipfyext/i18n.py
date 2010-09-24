# -*- coding: utf-8 -*-
"""
    tipfyext.i18n
    ~~~~~~~~~~~~~

    Internationalization extension.

    This extension provides internationalization utilities: a translations
    store, hooks to set locale for the current request, functions to manipulate
    dates according to timezones or translate and localize strings and dates.

    It uses `Babel <http://babel.edgewall.org/>`_ to manage translations of
    strings and localization of dates and times, and
    `gae-pytz <http://code.google.com/p/gae-pytz/>`_ to handle timezones.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime
import os

from babel import Locale, dates, numbers, support

from pytz.gae import pytz

from werkzeug import LocalProxy

from tipfy import Tipfy

__version__ = '0.7.1'
__version_info__ = tuple(int(n) for n in __version__.split('.'))

#: Default configuration values for this module. Keys are:
#:
#: locale
#:     The application default locale code. Default is ``en_US``.
#:     timezone: The application default timezone according to the Olson
#:     database. Default is ``America/Chicago``.
#:
#: cookie_name
#:     Cookie name used to save requested locale, in case cookies are used.
#:
#: locale_request_lookup
#:     A list of tuples (method, key) to search
#:     for the locale to be loaded for the current request. The methods are
#:     searched in order until a locale is found. Available methods are:
#:
#:     - args: gets the locale code from ``GET`` arguments.#:
#:     - form: gets the locale code from ``POST`` arguments.
#:     - cookies: gets the locale code from a cookie.
#:     - rule_args: gets the locale code from the keywords in the current
#:       URL rule.
#:
#:     If none of the methods find a locale code, uses the default locale.
#:     Default is ``[('args', 'lang'), ('cookies', 'tipfy.locale')]``: gets
#:     the locale from a ``lang`` parameter set in ``GET``, and if not set
#:     tries to get it from a cookie named ``tipfy.locale``.
#:
#: date_formats
#:     Default date formats for datetime, date and time.
default_config = {
    'locale':                'en_US',
    'timezone':              'America/Chicago',
    'cookie_name':           'locale',
    'locale_request_lookup': [('args', 'lang'), ('cookies', 'locale')],
    'date_formats': {
        'time':             'medium',
        'date':             'medium',
        'datetime':         'medium',
        'time.short':       None,
        'time.medium':      None,
        'time.full':        None,
        'time.long':        None,
        'date.short':       None,
        'date.medium':      None,
        'date.full':        None,
        'date.long':        None,
        'datetime.short':   None,
        'datetime.medium':  None,
        'datetime.full':    None,
        'datetime.long':    None,
    },
}

# Cache for loaded translations.
_translations = {}


class I18nMiddleware(object):
    """``tipfy.RequestHandler`` middleware that saves the current locale in
    a cookie at the end of request, if it differs from the default locale.
    """
    def after_dispatch(self, handler, response):
        """Saves current locale in a cookie.

        :param handler:
            The current ``tipfy.RequestHandler`` instance.
        :param response:
            The current ``tipfy.Response`` instance.
        :returns:
            None.
        """
        config = handler.app.get_config(__name__)
        locale = handler.request.context.get('locale', config.get('locale'))
        # Persist locale using a cookie when it differs from default.
        response.set_cookie(config.get('cookie_name'), value=locale,
            max_age=(86400 * 30))

        return response


def get_locale():
    """Returns the current locale code. Forces loading translations for the
    current request if it was not set already.

    :returns:
        The current locale code, e.g., ``en_US``.
    """
    ctx = Tipfy.request.context
    value = ctx.get('locale', None)
    if value is not None:
        return value

    set_translations_from_request()
    return ctx.get('locale')


def get_translations():
    """Returns the current translations object. Forces loading translations for
    the current request if it was not set already.

    :returns:
        A ``babel.support.Translations`` object.
    """
    ctx = Tipfy.request.context
    value = ctx.get('translations', None)
    if value is not None:
        return value

    set_translations_from_request()
    return ctx.get('translations')


def set_translations(locale):
    """Sets the locale and translations object for the current request. Most
    functions in this module depends on the translations object being set to
    work properly.

    :param locale:
        The locale code. For example, ``en_US`` or ``pt_BR``.
    :returns:
        None.
    """
    if locale not in _translations:
        locales = list(set([locale, Tipfy.app.get_config(__name__, 'locale')]))
        _translations[locale] = support.Translations.load('locale', locales,
            'messages')

    ctx = Tipfy.request.context
    ctx['locale'] = locale
    ctx['translations'] = _translations[locale]


def set_translations_from_request():
    """Sets a translations object for the current request.

    It will use the configuration for ``locale_request_lookup`` to search for
    a key in ``GET``, ``POST``, cookie or keywords in the current URL rule.
    The configuration defines the search order. If no locale is set in any of
    these, uses the default locale set in config.

    By default it gets the locale from a ``lang`` GET parameter, and if not
    set tries to get it from a cookie. This is represented by the default
    configuration value ``[('args', 'lang'), ('cookies', 'tipfy.locale')]``.

    :returns:
        None.
    """
    locale = None
    request = Tipfy.request
    for method, key in Tipfy.app.get_config(__name__, 'locale_request_lookup'):
        if method in ('args', 'form', 'cookies'):
            # Get locale from GET, POST or cookies.
            locale = getattr(request, method).get(key, None)
        elif method == 'rule_args':
            # Get locale from current URL rule keywords.
            locale = request.rule_args.get(key, None)

        if locale is not None:
            break
    else:
        locale = Tipfy.app.get_config(__name__, 'locale')

    set_translations(locale)


def list_translations():
    """Returns a list of all the locales translations exist for.  The
    list returned will be filled with actual locale objects and not just
    strings.

    :returns:
        A list of ``babel.Locale`` objects.
    """
    if not os.path.isdir('locale'):
        return []

    result = []
    for folder in sorted(os.listdir('locale')):
        if os.path.isdir(os.path.join('locale', folder, 'LC_MESSAGES')):
            result.append(Locale.parse(folder))

    return result


def is_default_locale():
    """Returns True if locale is set to the default locale.

    :returns:
        True if locale is set to the default locale, False otherwise.
    """
    ctx = Tipfy.request.context
    return ctx.get('locale', None) == Tipfy.app.get_config(__name__, 'locale')


def gettext(string, **variables):
    """Translates a given string according to the current locale.

    :param string:
        The string to be translated.
    :param variables:
        Variables to format the returned string.
    :returns:
        The translated string.
    """
    return get_translations().ugettext(string) % variables


def ngettext(singular, plural, n, **variables):
    """Translates a possible pluralized string according to the current locale.

    :param singular:
        The singular for of the string to be translated.
    :param plural:
        The plural for of the string to be translated.
    :param n:
        An integer indicating if this is a singular or plural. If greater
        than 1, it is a plural.
    :param variables:
        Variables to format the returned string.
    :returns:
        The translated string.
    """
    return get_translations().ungettext(singular, plural, n) % variables


def lazy_gettext(string, **variables):
    """A lazy version of [[#gettext]].

    :param string:
        The string to be translated.
    :param variables:
        Variables to format the returned string.
    :returns:
        A ``babel.support.LazyProxy`` object that when accessed translates
        the string.
    """
    return support.LazyProxy(gettext, string, **variables)


def lazy_ngettext(singular, plural, n, **variables):
    """A lazy version of [[#ngettext]].

    :param singular:
        The singular for of the string to be translated.
    :param plural:
        The plural for of the string to be translated.
    :param n:
        An integer indicating if this is a singular or plural. If greater
        than 1, it is a plural.
    :param variables:
        Variables to format the returned string.
    :returns:
        A ``babel.support.LazyProxy`` object that when accessed translates
        the string.
    """
    return support.LazyProxy(ngettext, singular, plural, n, **variables)


def get_timezone(timezone=None):
    """Returns a ``datetime.tzinfo`` object for the given timezone. This is
    called by [[#format_datetime]] and [[#format_time]] when a tzinfo
    is not provided.

    :param timezone:
        The timezone name from the Olson database, e.g.: ``America/Chicago``.
        If not set, uses the default configuration value.
    :returns:
        A ``datetime.tzinfo`` object.
    """
    return pytz.timezone(timezone or Tipfy.app.get_config(__name__, 'timezone'))


def to_local_timezone(datetime):
    """Returns a datetime object converted to the local timezone.

    This function derives from `Kay <http://code.google.com/p/kay-framework/>`_.

    :param datetime:
        A ``datetime`` object.
    :returns:
        A ``datetime`` object normalized to a timezone.
    """
    tzinfo = get_timezone()
    if datetime.tzinfo is None:
        datetime = datetime.replace(tzinfo=pytz.UTC)

    return tzinfo.normalize(datetime.astimezone(tzinfo))


def to_utc(datetime):
    """Returns a datetime object converted to UTC and without tzinfo.

    This function derives from `Kay <http://code.google.com/p/kay-framework/>`_.

    :param datetime:
        A ``datetime`` object.
    :returns:
        A naive ``datetime`` object (no timezone), converted to UTC.
    """
    if datetime.tzinfo is None:
        datetime = get_timezone().localize(datetime)

    return datetime.astimezone(pytz.UTC).replace(tzinfo=None)


def _get_format(key, format):
    """A small helper for the datetime formatting functions. Returns a format
    name or pattern to be used by Babel date format functions.

    This function derives from `Flask-Babel <http://pypi.python.org/pypi/Flask-Babel/>`_

    :param key:
        A format key to be get from config: ``date``, ``datetime`` or ``time``.
    :param format:
        The format to be returned. Valid values are "short", "medium",
        "long", "full" or a custom date/time pattern.
    :returns:
        A format name or pattern to be used by Babel date format functions.
    """
    config = Tipfy.app.get_config(__name__)['date_formats']

    if format is None:
        format = config[key]

    if format in ('short', 'medium', 'full', 'long'):
        rv = config['%s.%s' % (key, format)]
        if rv is not None:
            format = rv

    return format


def format_date(date=None, format=None, locale=None, rebase=True):
    """Returns a date formatted according to the given pattern and following
    the current locale.

    :param date:
        A ``date`` or ``datetime`` object. If None, the current date in UTC
        is used.
    :param format:
        The format to be returned. Valid values are "short", "medium",
        "long", "full" or a custom date/time pattern. Example outputs:

        - short:  11/10/09
        - medium: Nov 10, 2009
        - long:   November 10, 2009
        - full:   Tuesday, November 10, 2009

    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :param rebase:
        If True, converts the date to the currently loaded timezone.
    :returns:
        A formatted date in unicode.
    """
    format = _get_format('date', format)
    locale = locale or get_locale()

    if rebase and isinstance(date, datetime):
        date = to_local_timezone(date)

    return dates.format_date(date, format, locale=locale)


def format_datetime(datetime=None, format=None, locale=None, timezone=None,
    rebase=True):
    """Returns a date and time formatted according to the given pattern and
    following the current locale and timezone.

    :param datetime:
        A ``datetime`` object. If None, the current date and time in UTC
        is used.
    :param format:
        The format to be returned. Valid values are "short", "medium",
        "long", "full" or a custom date/time pattern. Example outputs:

        - short:  11/10/09 4:36 PM
        - medium: Nov 10, 2009 4:36:05 PM
        - long:   November 10, 2009 4:36:05 PM +0000
        - full:   Tuesday, November 10, 2009 4:36:05 PM World (GMT) Time

    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :param timezone:
        The timezone name from the Olson database, e.g.:
        'America/Chicago'. If not set, uses the default returned by
        :func:`get_timezone`.
    :param rebase:
        If True, converts the datetime to the currently loaded timezone.
    :returns:
        A formatted date and time in unicode.
    """
    format = _get_format('datetime', format)
    locale = locale or get_locale()

    kwargs = {}
    if rebase:
        kwargs['tzinfo'] = get_timezone(timezone)

    return dates.format_datetime(datetime, format, locale=locale, **kwargs)


def format_time(time=None, format=None, locale=None, timezone=None,
    rebase=True):
    """Returns a time formatted according to the given pattern and following
    the current locale and timezone.

    :param time:
        A ``time`` or ``datetime`` object. If None, the current
        time in UTC is used.
    :param format:
        The format to be returned. Valid values are "short", "medium",
        "long", "full" or a custom date/time pattern. Example outputs:

        - short:  4:36 PM
        - medium: 4:36:05 PM
        - long:   4:36:05 PM +0000
        - full:   4:36:05 PM World (GMT) Time

    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :param timezone:
        The timezone name from the Olson database, e.g.: ``America/Chicago``.
        If not set, uses the default returned by :func:`get_timezone`.
    :param rebase:
        If True, converts the time to the currently loaded timezone.
    :returns:
        A formatted time in unicode.
    """
    format = _get_format('time', format)
    locale = locale or get_locale()

    kwargs = {}
    if rebase:
        kwargs['tzinfo'] = get_timezone(timezone)

    return dates.format_time(time, format, locale=locale, **kwargs)


def format_timedelta(datetime_or_timedelta, granularity='second',
    threshold=.85, locale=None):
    """Formats the elapsed time from the given date to now or the given
    timedelta. This currently requires an unreleased development version
    of Babel.

    :param datetime_or_timedelta:
        A ``timedelta`` object representing the time difference to format,
        or a ``datetime`` object in UTC.
    :param granularity:
        Determines the smallest unit that should be displayed, the value can
        be one of "year", "month", "week", "day", "hour", "minute" or "second".
    :param threshold:
        Factor that determines at which point the presentation switches to
        the next higher unit.
    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :returns:
        A string with the elapsed time.
    """
    locale = locale or get_locale()
    if isinstance(datetime_or_timedelta, datetime):
        datetime_or_timedelta = datetime.utcnow() - datetime_or_timedelta

    return dates.format_timedelta(datetime_or_timedelta, granularity,
        threshold=threshold, locale=locale)


def format_number(number, locale=None):
    """Returns the given number formatted for a specific locale.

    .. code-block:: python

       >>> format_number(1099, locale='en_US')
       u'1,099'

    :param number:
        The number to format.
    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :returns:
        The formatted number.
    """
    locale = locale or get_locale()
    return numbers.format_number(number, locale=locale)

def format_decimal(number, format=None, locale=None):
    """Returns the given decimal number formatted for a specific locale.

    .. code-block:: python

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

    .. code-block:: python

       >>> format_decimal(12345.5, locale='en_US')
       u'12,345.5'

    :param number:
        The number to format.
    :param format:
        Notation format.
    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :returns:
        The formatted decimal number.
    """
    locale = locale or get_locale()
    return numbers.format_decimal(number, format=format, locale=locale)


def format_currency(number, currency, format=None, locale=None):
    """Returns a formatted currency value.

    .. code-block:: python

       >>> format_currency(1099.98, 'USD', locale='en_US')
       u'$1,099.98'
       >>> format_currency(1099.98, 'USD', locale='es_CO')
       u'US$\\xa01.099,98'
       >>> format_currency(1099.98, 'EUR', locale='de_DE')
       u'1.099,98\\xa0\\u20ac'

    The pattern can also be specified explicitly:

    .. code-block:: python

       >>> format_currency(1099.98, 'EUR', u'\\xa4\\xa4 #,##0.00', locale='en_US')
       u'EUR 1,099.98'

    :param number:
        The number to format.
    :param currency:
        The currency code.
    :param format:
        Notation format.
    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :returns:
        The formatted currency value.
    """
    locale = locale or get_locale()
    return numbers.format_currency(number, currency, format=format,
        locale=locale)


def format_percent(number, format=None, locale=None):
    """Returns formatted percent value for a specific locale.

    .. code-block:: python

       >>> format_percent(0.34, locale='en_US')
       u'34%'
       >>> format_percent(25.1234, locale='en_US')
       u'2,512%'
       >>> format_percent(25.1234, locale='sv_SE')
       u'2\\xa0512\\xa0%'

    The format pattern can also be specified explicitly:

    .. code-block:: python

       >>> format_percent(25.1234, u'#,##0\u2030', locale='en_US')
       u'25,123\u2030'

    :param number:
        The percent number to format
    :param format:
        Notation format.
    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :returns:
        The formatted percent number.
    """
    locale = locale or get_locale()
    return numbers.format_percent(number, format=format, locale=locale)


def format_scientific(number, format=None, locale=None):
    """Returns value formatted in scientific notation for a specific locale.

    .. code-block:: python

       >>> format_scientific(10000, locale='en_US')
       u'1E4'

    The format pattern can also be specified explicitly:

    .. code-block:: python

       >>> format_scientific(1234567, u'##0E00', locale='en_US')
       u'1.23E06'

    :param number:
        The number to format.
    :param format:
        Notation format.
    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :returns:
        Value formatted in scientific notation.
    """
    locale = locale or get_locale()
    return numbers.format_scientific(number, format=format, locale=locale)


def parse_date(string, locale=None):
    """Parses a date from a string.

    This function uses the date format for the locale as a hint to determine
    the order in which the date fields appear in the string.

    .. code-block:: python

       >>> parse_date('4/1/04', locale='en_US')
       datetime.date(2004, 4, 1)
       >>> parse_date('01.04.2004', locale='de_DE')
       datetime.date(2004, 4, 1)

    :param string:
        The string containing the date.
    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :returns:
        The parsed date object.
    """
    locale = locale or get_locale()
    return dates.parse_date(string, locale=locale)


def parse_datetime(string, locale=None):
    """Parses a date and time from a string.

    This function uses the date and time formats for the locale as a hint to
    determine the order in which the time fields appear in the string.

    :param string:
        The string containing the date and time.
    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :returns:
        The parsed datetime object.
    """
    locale = locale or get_locale()
    return dates.parse_datetime(string, locale=locale)


def parse_time(string, locale=None):
    """Parses a time from a string.

    This function uses the time format for the locale as a hint to determine
    the order in which the time fields appear in the string.

    .. code-block:: python

       >>> parse_time('15:30:00', locale='en_US')
       datetime.time(15, 30)

    :param string:
        The string containing the time.
    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :returns:
        The parsed time object.
    """
    locale = locale or get_locale()
    return dates.parse_time(string, locale=locale)


def parse_number(string, locale=None):
    """Parses localized number string into a long integer.

    .. code-block:: python

       >>> parse_number('1,099', locale='en_US')
       1099L
       >>> parse_number('1.099', locale='de_DE')
       1099L

    When the given string cannot be parsed, an exception is raised:

    .. code-block:: python

       >>> parse_number('1.099,98', locale='de')
       Traceback (most recent call last):
           ...
       NumberFormatError: '1.099,98' is not a valid number

    :param string:
        The string to parse.
    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :returns:
        The parsed number.
    :raises:
        ``NumberFormatError`` if the string can not be converted to a number.
    """
    locale = locale or get_locale()
    return numbers.parse_number(string, locale=locale)


def parse_decimal(string, locale=None):
    """Parses localized decimal string into a float.

    .. code-block:: python

       >>> parse_decimal('1,099.98', locale='en_US')
       1099.98
       >>> parse_decimal('1.099,98', locale='de')
       1099.98

    When the given string cannot be parsed, an exception is raised:

    .. code-block:: python

       >>> parse_decimal('2,109,998', locale='de')
       Traceback (most recent call last):
           ...
       NumberFormatError: '2,109,998' is not a valid decimal number

    :param string:
        The string to parse.
    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :returns:
        The parsed decimal number.
    :raises:
        ``NumberFormatError`` if the string can not be converted to a
        decimal number.
    """
    locale = locale or get_locale()
    return numbers.parse_decimal(string, locale=locale)


def get_timezone_name(dt_or_tzinfo, locale=None):
    """Returns a representation of the given timezone using "location format".

    The result depends on both the local display name of the country and the
    city assocaited with the time zone:

    .. code-block:: python

       >>> from pytz import timezone
       >>> tz = timezone('America/St_Johns')
       >>> get_timezone_location(tz, locale='de_DE')
       u"Kanada (St. John's)"
       >>> tz = timezone('America/Mexico_City')
       >>> get_timezone_location(tz, locale='de_DE')
       u'Mexiko (Mexiko-Stadt)'

    If the timezone is associated with a country that uses only a single
    timezone, just the localized country name is returned:

    .. code-block:: python

       >>> tz = timezone('Europe/Berlin')
       >>> get_timezone_name(tz, locale='de_DE')
       u'Deutschland'

    :param dt_or_tzinfo:
        The ``datetime`` or ``tzinfo`` object that determines
        the timezone; if None, the current date and time in UTC is assumed.
    :param locale:
        A locale code. If not set, uses the currently loaded locale.
    :returns:
        The localized timezone name using location format.
    """
    locale = locale or get_locale()
    return dates.get_timezone_name(dt_or_tzinfo, locale=locale)


# Common alias to gettext.
_ = gettext

# Current translations.
translations = LocalProxy(lambda: get_translations())

# Old names.
get_tzinfo = get_timezone
