# -*- coding: utf-8 -*-
"""
    tipfy.i18n
    ~~~~~~~~~~

    Internationalization utilities.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from babel.support import Translations as BabelTranslations, LazyProxy
from babel.dates import format_date as babel_format_date, \
    format_datetime as babel_format_datetime, format_time as babel_format_time
from tipfy.app import local, config


class Translations(object):
    """Stores Babel Translations instances."""
    def __init__(self, locale=None):
        self._translations = {}
        if locale:
            self.set_locale(locale)

    def set_requested_locale(self):
        """Sets the locale for a single request."""
        # Get locale from a 'lang' query parameter, and if not set try to get
        # from a cookie. As last option, use the locale set in config.
        locale = local.request.args.get('lang',
            local.request.cookies.get('tipfy.locale', config.locale))

        self.set_locale(locale)

        if locale != config.locale:
            # Persist locale using a cookie when it differs from default.
            local.response.set_cookie('tipfy.locale', value=locale,
                max_age=(86400 * 30))

    def set_locale(self, locale):
        """Sets the current locale. Instantiates the Translations object if not
        already instantiated.
        """
        if locale not in self._translations:
            options = list(set([locale, config.locale]))
            self._translations[locale] = BabelTranslations.load('locale',
                options, 'messages')
        local.locale = locale
        local.translations = self._translations[locale]


# Some functions borrowed from Zine: http://zine.pocoo.org/.
def get_translations():
    """Get the active translations or `None`."""
    return getattr(local, 'translations', None)


def get_locale():
    """Get the active locale or `None`."""
    return getattr(local, 'locale', None)


def gettext(string):
    """Translate a given string to the language of the application."""
    translations = getattr(local, 'translations', None)
    if translations is None:
        return unicode(string, 'utf-8')
    return unicode(translations.gettext(string), 'utf-8')


def ngettext(singular, plural, n):
    """Translate the possible pluralized string to the language of the
    application.
    """
    translations = getattr(local, 'translations', None)
    if translations is None:
        if n == 1:
            return unicode(singular, 'utf-8')
        return unicode(plural, 'utf-8')
    return unicode(translations.ngettext(singular, plural, n), 'utf-8')


def lazy_gettext(string):
    """A lazy version of `gettext`."""
    return LazyProxy(gettext, string)


def lazy_ngettext(singular, plural, n):
    """A lazy version of `ngettext`."""
    return LazyProxy(ngettext, singular, plural, n)


def format_date(value=None, format='medium'):
    return babel_format_date(date=value + config.time_diff, format=format,
        locale=get_locale())


def format_datetime(value=None, format='medium', tzinfo=None):
    return babel_format_datetime(datetime=value + config.time_diff,
        format=format, tzinfo=tzinfo, locale=get_locale())


def format_time(value=None, format='medium', tzinfo=None):
    return babel_format_time(time=value + config.time_diff, format=format,
        tzinfo=tzinfo, locale=get_locale())


_ = gettext
