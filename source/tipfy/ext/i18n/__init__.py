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
import datetime
from babel.support import Translations as BabelTranslations, LazyProxy
from babel.dates import format_date as babel_format_date, \
    format_datetime as babel_format_datetime, format_time as babel_format_time

from tipfy import local, app, request, response

# Set proxy for the current locale code and translations object.
local.locale = local.translations = None
locale = local('locale')
translations = local('translations')

# Translations object cached in the module.
_translations = None


class Translations(object):
    """Stores Babel Translations instances."""
    def __init__(self, locale):
        self._translations = {}
        self.set_locale(locale)

    def set_locale(self, locale):
        if locale not in self._translations:
            options = list(set([locale, app.config.locale]))
            self._translations[locale] = BabelTranslations.load('locale',
                options, 'messages')

        local.locale = locale
        local.translations = self._translations[locale]


def get_translations():
    """Returns the Translations object."""
    global _translations
    if _translations is None:
        _translations = Translations(app.config.locale)

    return _translations


def set_requested_locale():
    """Called on pre_handler_init. Sets the locale for a single request."""
    # Get locale from a 'lang' query parameter, and if not set try to get
    # from a cookie. As last option, use the locale set in config.
    locale = request.args.get('lang', request.cookies.get('tipfy.locale',
        app.config.locale))

    get_translations().set_locale(locale)

    if locale != app.config.locale:
        # Persist locale using a cookie when it differs from default.
        response.set_cookie('tipfy.locale', value=locale, max_age=(86400 * 30))


# Some functions borrowed from Zine: http://zine.pocoo.org/.
def gettext(string):
    """Translate a given string to the language of the application."""
    return unicode(translations.gettext(string), 'utf-8')


def ngettext(singular, plural, n):
    """Translate the possible pluralized string to the language of the
    application.
    """
    return unicode(translations.ngettext(singular, plural, n), 'utf-8')


def lazy_gettext(string):
    """A lazy version of `gettext`."""
    return LazyProxy(gettext, string)


def lazy_ngettext(singular, plural, n):
    """A lazy version of `ngettext`."""
    return LazyProxy(ngettext, singular, plural, n)


def format_date(value=None, format='medium'):
    time_diff = app.config.time_diff or datetime.timedelta()
    return babel_format_date(date=value + time_diff, format=format,
        locale=local.locale)


def format_datetime(value=None, format='medium', tzinfo=None):
    time_diff = app.config.time_diff or datetime.timedelta()
    return babel_format_datetime(datetime=value + time_diff, format=format,
        tzinfo=tzinfo, locale=local.locale)


def format_time(value=None, format='medium', tzinfo=None):
    time_diff = app.config.time_diff or datetime.timedelta()
    return babel_format_time(time=value + time_diff, format=format,
        tzinfo=tzinfo, locale=local.locale)


_ = gettext
