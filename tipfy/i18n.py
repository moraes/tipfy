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

    Several ideas were borrowed from
    `Flask-Babel <http://pypi.python.org/pypi/Flask-Babel/>`_

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime
import os

from babel import Locale, dates, numbers, support

from pytz.gae import pytz

from werkzeug import LocalProxy

from tipfy import Tipfy

#: Default configuration values for this module. Keys are:
#:
#: locale
#:     The application default locale code. Default is ``en_US``.
#:     timezone: The application default timezone according to the Olson
#:     database. Default is ``America/Chicago``.
#:
#: session_key
#:     Session key used to save requested locale, in case sessions are used.
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
#:     Default is ``[('args', 'lang'), ('session', '_locale')]``: gets
#:     the locale from a ``lang`` parameter set in ``GET``, and if not set
#:     tries to get it from the session key ``_locale``.
#:
#: date_formats
#:     Default date formats for datetime, date and time.
default_config = {
    'locale':                'en_US',
    'timezone':              'America/Chicago',
    'session_key':           '_locale',
    'locale_request_lookup': [('args', 'lang'), ('session', '_locale')],
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


class I18nMiddleware(object):
    """``tipfy.RequestHandler`` middleware that saves the current locale in
    the session at the end of request, if it differs from the current value
    stored in the session.
    """
    def after_dispatch(self, handler, response):
        """Saves current locale in the session.

        :param handler:
            The current ``tipfy.RequestHandler`` instance.
        :param response:
            The current ``tipfy.Response`` instance.
        """
        session = handler.request.session
        i18n = handler.request.i18n_store
        session_key = i18n.config['session_key']

        if i18n.locale != session.get(session_key):
            # Only save if it differs from original session value.
            session[session_key] = i18n.locale

        return response


class I18nStore(object):
    #: Loaded translations.
    loaded_translations = None
    #: Current translation.
    translations = None
    #: Current locale.
    locale = None
    #: Current timezone.
    timezone = None
    #: Current tzinfo.
    tzinfo = None

    def __init__(self, app):
        self.app = app
        self.loaded_translations = {}

        config = app.config[__name__]
        self.default_locale = config['locale']
        self.default_timezone = config['timezone']
        self.date_formats = config['date_formats']
        self.config = config

        # Initialize using default config values.
        self.set_locale(self.default_locale)
        self.set_timezone(self.default_timezone)

    def set_locale(self, locale):
        self.locale = locale
        if locale not in self.loaded_translations:
            locales = [locale]
            if locale != self.default_locale:
                locales.append(self.default_locale)

            self.loaded_translations[locale] = self.load_translations(locales)

        self.translations = self.loaded_translations[locale]

    def set_timezone(self, timezone):
        self.timezone = timezone
        self.tzinfo = pytz.timezone(timezone)

    def set_locale_for_request(self, request):
        """Sets a translations object for the current request.

        It will use the configuration for ``locale_request_lookup`` to search
        for a key in ``GET``, ``POST``, session, cookie or keywords in the
        current URL rule. The configuration defines the search order. If no
        locale is set in any of these, uses the default locale set in config.

        By default it gets the locale from a ``lang`` GET parameter, and if
        not set tries to get it from a cookie. This is represented by the
        default configuration value ``[('args', 'lang'), ('cookies',
        'tipfy.locale')]``.
        """
        locale = None
        for method, key in self.config['locale_request_lookup']:
            # Get locale from GET, POST, session, cookies or rule_args.
            locale = getattr(request, method).get(key, None)
            if locale is not None:
                break
        else:
            locale = self.default_locale

        self.set_locale(locale)

    def load_translations(self, locales, dirname='locale', domain='messages'):
        return support.Translations.load(dirname, locales, domain)

    def gettext(self, string, **variables):
        """Translates a given string according to the current locale.

        :param string:
            The string to be translated.
        :param variables:
            Variables to format the returned string.
        :returns:
            The translated string.
        """
        return self.translations.ugettext(string) % variables

    def ngettext(self, singular, plural, n, **variables):
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
        return self.translations.ungettext(singular, plural, n) % variables

    def _get_format(self, key, format):
        """A helper for the datetime formatting functions. Returns a format
        name or pattern to be used by Babel date format functions.

        :param key:
            A format key to be get from config. Valid values are "date",
            "datetime" or "time".
        :param format:
            The format to be returned. Valid values are "short", "medium",
            "long", "full" or a custom date/time pattern.
        :returns:
            A format name or pattern to be used by Babel date format functions.
        """
        if format is None:
            format = self.date_formats.get(key)

        if format in ('short', 'medium', 'full', 'long'):
            rv = self.date_formats.get('%s.%s' % (key, format))
            if rv is not None:
                format = rv

        return format

    def to_local_timezone(self, datetime):
        """Returns a datetime object converted to the local timezone.

        This function derives from `Kay <http://code.google.com/p/kay-framework/>`_.

        :param datetime:
            A ``datetime`` object.
        :returns:
            A ``datetime`` object normalized to a timezone.
        """
        if datetime.tzinfo is None:
            datetime = datetime.replace(tzinfo=pytz.UTC)

        return self.tzinfo.normalize(datetime.astimezone(self.tzinfo))

    def to_utc(self, datetime):
        """Returns a datetime object converted to UTC and without tzinfo.

        This function derives from `Kay <http://code.google.com/p/kay-framework/>`_.

        :param datetime:
            A ``datetime`` object.
        :returns:
            A naive ``datetime`` object (no timezone), converted to UTC.
        """
        if datetime.tzinfo is None:
            datetime = self.tzinfo.localize(datetime)

        return datetime.astimezone(pytz.UTC).replace(tzinfo=None)

    def format_date(self, date=None, format=None, locale=None, rebase=True):
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
        format = self._get_format('date', format)
        locale = locale or self.locale

        if rebase and isinstance(date, datetime):
            date = self.to_local_timezone(date)

        return dates.format_date(date, format, locale=locale)

    def format_datetime(self, datetime=None, format=None, locale=None,
        timezone=None, rebase=True):
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
        format = self._get_format('datetime', format)
        locale = locale or self.locale

        kwargs = {}
        if rebase:
            if timezone:
                kwargs['tzinfo'] = pytz.timezone(timezone)
            else:
                kwargs['tzinfo'] = self.tzinfo

        return dates.format_datetime(datetime, format, locale=locale, **kwargs)

    def format_time(self, time=None, format=None, locale=None, timezone=None,
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
        format = self._get_format('time', format)
        locale = locale or self.locale

        kwargs = {}
        if rebase:
            if timezone:
                kwargs['tzinfo'] = pytz.timezone(timezone)
            else:
                kwargs['tzinfo'] = self.tzinfo

        return dates.format_time(time, format, locale=locale, **kwargs)


def set_locale(locale):
    return Tipfy.request.i18n_store.set_locale(locale)


def gettext(string, **variables):
    return Tipfy.request.i18n_store.gettext(string, **variables)


def ngettext(singular, plural, n, **variables):
    return Tipfy.request.i18n_store.ngettext(singular, plural, n, **variables)


def to_local_timezone(datetime):
    return Tipfy.request.i18n_store.to_local_timezone(datetime)


def to_utc(datetime):
    return Tipfy.request.i18n_store.to_utc(datetime)


def format_date(date=None, format=None, locale=None, rebase=True):
    return Tipfy.request.i18n_store.format_date(date, format, locale, rebase)


def format_datetime(datetime=None, format=None, locale=None, timezone=None,
    rebase=True):
    return Tipfy.request.i18n_store.format_datetime(datetime, format, locale,
        timezone, rebase)


def format_time(time=None, format=None, locale=None, timezone=None,
    rebase=True):
    return Tipfy.request.i18n_store.format_time(time, format, locale, timezone,
        rebase)


def lazy_gettext(string, **variables):
    """A lazy version of :func:`gettext`.

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
    """A lazy version of :func:`ngettext`.

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


# Alias to gettext.
_ = gettext
