# -*- coding: utf-8 -*-
"""
    tipfy.plugins.i18n
    ~~~~~~~~~~~~~~~~~~

    Internationalization plugin.

    To work properly, this requires the following definitions to be added to
    the config file:

    plugins = [
        ('post_wsgi_app_init', 'tipfy.plugins.i18n:set_translations'),
        ('post_request_set', 'tipfy.plugins.i18n:set_requested_locale'),
        ('post_env_set', 'tipfy.plugins.i18n:set_env_i18n'),
    ]

    It also requires the babel module to be added to the lib dir. Babel can be
    downloaded at http://babel.edgewall.org/

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from babel.support import Translations as BabelTranslations, LazyProxy
from babel.dates import format_date as babel_format_date, \
    format_datetime as babel_format_datetime, format_time as babel_format_time
from tipfy.app import local, config
from jinja2.ext import i18n

import config

def set_translations(wsgi_app):
    """Called on post_wsgi_app_init. Initializes translations."""
    wsgi_app.translations = Translations(config.locale)


def set_requested_locale(wsgi_app):
    """Called on pre_handler_init. Sets the locale for a single request."""
    # Get locale from a 'lang' query parameter, and if not set try to get
    # from a cookie. As last option, use the locale set in config.
    locale = local.request.args.get('lang',
        local.request.cookies.get('tipfy.locale', config.locale))

    wsgi_app.translations.set_locale(locale)

    if locale != config.locale:
        # Persist locale using a cookie when it differs from default.
        local.response.set_cookie('tipfy.locale', value=locale,
            max_age=(86400 * 30))


def set_env_i18n(env):
    """Called on 'post_env_set'. Sets i18n in Jinja2."""
    env.globals.update({
        'format_date': format_date,
        'format_datetime': format_datetime,
        'format_time': format_time,
    })
    env.extensions[i18n.identifier] = i18n(env)
    env.install_gettext_translations(local.translations)


class Translations(object):
    """Stores Babel Translations instances."""
    def __init__(self, locale=None):
        self._translations = {}
        if locale:
            self.set_locale(locale)

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
