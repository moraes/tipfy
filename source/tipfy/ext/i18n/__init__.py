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
from babel.support import Translations, LazyProxy
from babel.dates import format_date as babel_format_date, \
    format_datetime as babel_format_datetime, format_time as babel_format_time

from tipfy import local, app, request, response

# Set proxy for the current locale code and translations object.
local.locale = local.translations = None
locale = local('locale')
translations = local('translations')

# Cache loaded translations in the module
_translations = {}


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


# Some functions borrowed from Zine: http://zine.pocoo.org/.
def gettext(string):
    """Translate a given string to the language of the application."""
    return unicode(local.translations.gettext(string), 'utf-8')


def ngettext(singular, plural, n):
    """Translate the possible pluralized string to the language of the
    application.
    """
    return unicode(local.translations.ngettext(singular, plural, n), 'utf-8')


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
