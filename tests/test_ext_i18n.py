# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.i18n
"""
import datetime
import gettext as gettext_stdlib
import unittest

from nose.tools import raises

import _base

from babel.numbers import NumberFormatError

import tipfy
from tipfy.ext import i18n

class Request(object):
    """A fake request object with GET, POST and cookies."""
    def __init__(self, args=None, form=None, cookies=None):
        self.args = args or {}
        self.form = form or {}
        self.cookies= cookies or {}

class Response(object):
    """A dummy response to test setting locale cookies."""
    def __init__(self):
        self.cookies = {}

    def set_cookie(self, name, value, **kwargs):
        self.cookies[name] = value


class TestI18nMiddleware(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_post_dispatch(self):
        middleware = i18n.I18nMiddleware()

        tipfy.local.app = tipfy.WSGIApplication({
            'tipfy.ext.i18n': {
                'locale': 'jp_JP',
            },
        })

        response = Response()
        response = middleware.post_dispatch(None, response)
        assert isinstance(response, Response)
        assert response.cookies == {}

        tipfy.local.locale = 'ru_RU'
        response = Response()
        response = middleware.post_dispatch(None, response)
        assert response.cookies == {'tipfy.locale': 'ru_RU'}
        assert isinstance(response, Response)

    def test_pre_dispatch_handler(self):
        tipfy.local.app = tipfy.WSGIApplication({
            'tipfy.ext.i18n': {
                'locale_request_lookup': [('args', 'language')],
            },
        })
        tipfy.local.request = Request(args={'language': 'es_ES'})

        middleware = i18n.I18nMiddleware()
        middleware.pre_dispatch_handler()
        assert tipfy.local.locale == 'es_ES'

    def test_post_dispatch_handler(self):
        middleware = i18n.I18nMiddleware()

        tipfy.local.app = tipfy.WSGIApplication({
            'tipfy.ext.i18n': {
                'locale': 'jp_JP',
            },
        })

        response = Response()
        response = middleware.post_dispatch_handler(response)
        assert isinstance(response, Response)
        assert response.cookies == {}

        tipfy.local.locale = 'ru_RU'
        response = Response()
        response = middleware.post_dispatch_handler(response)
        assert response.cookies == {'tipfy.locale': 'ru_RU'}
        assert isinstance(response, Response)


class TestI18n(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()
    #===========================================================================
    # Translations
    #===========================================================================
    def test_set_translations(self):
        assert getattr(tipfy.local, 'locale', None) is None
        assert getattr(tipfy.local, 'translations', None) is None

        i18n.set_translations('pt_BR')
        assert tipfy.local.locale == 'pt_BR'
        assert isinstance(tipfy.local.translations, gettext_stdlib.NullTranslations)

    def test_set_translations_from_request(self):
        tipfy.local.app = tipfy.WSGIApplication({
            'tipfy.ext.i18n': {
                'locale': 'jp_JP',
            },
        })
        tipfy.local.request = Request()

        i18n.set_translations_from_request()
        assert tipfy.local.locale == 'jp_JP'

    def test_set_translations_from_request_args(self):
        tipfy.local.app = tipfy.WSGIApplication({
            'tipfy.ext.i18n': {
                'locale_request_lookup': [('args', 'language')],
            },
        })
        tipfy.local.request = Request(args={'language': 'es_ES'})

        i18n.set_translations_from_request()
        assert tipfy.local.locale == 'es_ES'

    def test_set_translations_from_request_form(self):
        tipfy.local.app = tipfy.WSGIApplication({
            'tipfy.ext.i18n': {
                'locale_request_lookup': [('form', 'language')],
            },
        })
        tipfy.local.request = Request(form={'language': 'es_ES'})

        i18n.set_translations_from_request()
        assert tipfy.local.locale == 'es_ES'

    def test_set_translations_from_request_cookies(self):
        tipfy.local.app = tipfy.WSGIApplication({
            'tipfy.ext.i18n': {
                'locale_request_lookup': [('cookies', 'language')],
            },
        })
        tipfy.local.request = Request(cookies={'language': 'es_ES'})

        i18n.set_translations_from_request()
        assert tipfy.local.locale == 'es_ES'

    def test_set_translations_from_request_args_form_cookies(self):
        tipfy.local.app = tipfy.WSGIApplication({
            'tipfy.ext.i18n': {
                'locale_request_lookup': [('args', 'foo'), ('form', 'bar'), ('cookies', 'language')],
            },
        })
        tipfy.local.request = Request(cookies={'language': 'es_ES'})

        i18n.set_translations_from_request()
        assert tipfy.local.locale == 'es_ES'

    def test_set_translations_from_rule_args(self):
        tipfy.local.app = tipfy.WSGIApplication({
            'tipfy.ext.i18n': {
                'locale_request_lookup': [('rule_args', 'locale'),],
            },
        })
        tipfy.local.request = Request()

        tipfy.local.app.rule_args = {'locale': 'es_ES'}
        i18n.set_translations_from_request()
        assert tipfy.local.locale == 'es_ES'

        tipfy.local.app.rule_args = {'locale': 'pt_BR'}
        i18n.set_translations_from_request()
        assert tipfy.local.locale == 'pt_BR'

    def test_is_default_locale(self):
        app = tipfy.WSGIApplication()
        tipfy.local.locale = 'en_US'
        assert i18n.is_default_locale() is True
        tipfy.local.locale = 'pt_BR'
        assert i18n.is_default_locale() is False

        app = tipfy.WSGIApplication({'tipfy.ext.i18n': {'locale': 'pt_BR'}})
        tipfy.local.locale = 'en_US'
        assert i18n.is_default_locale() is False
        tipfy.local.locale = 'pt_BR'
        assert i18n.is_default_locale() is True

    #===========================================================================
    # gettext(), ngettext(), lazy_gettext(), lazy_ngettext()
    #===========================================================================

    @raises(AttributeError)
    def test_translations_not_set(self):
        i18n.gettext('foo')

    def test_gettext(self):
        i18n.set_translations('en_US')
        assert i18n.gettext('foo') == u'foo'

    def test_gettext_(self):
        i18n.set_translations('en_US')
        assert i18n._('foo') == u'foo'

    def test_ngettext(self):
        i18n.set_translations('en_US')
        assert i18n.ngettext('One foo', 'Many foos', 1) == u'One foo'
        assert i18n.ngettext('One foo', 'Many foos', 2) == u'Many foos'

    def test_lazy_gettext(self):
        i18n.set_translations('en_US')
        assert i18n.lazy_gettext('foo') == u'foo'

    def test_lazy_ngettext(self):
        i18n.set_translations('en_US')
        assert i18n.lazy_ngettext('One foo', 'Many foos', 1) == u'One foo'
        assert i18n.lazy_ngettext('One foo', 'Many foos', 2) == u'Many foos'

    #===========================================================================
    # Date formatting
    #===========================================================================
    def test_format_date(self):
        app = tipfy.WSGIApplication({'tipfy.ext.i18n': {'timezone': 'UTC'}})

        i18n.set_translations('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert i18n.format_date(value, format='short') == u'11/10/09'
        assert i18n.format_date(value, format='medium') == u'Nov 10, 2009'
        assert i18n.format_date(value, format='long') == u'November 10, 2009'
        assert i18n.format_date(value, format='full') == u'Tuesday, November 10, 2009'

    def test_format_date_pt_BR(self):
        app = tipfy.WSGIApplication({'tipfy.ext.i18n': {'timezone': 'UTC'}})

        i18n.set_translations('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert i18n.format_date(value, format='short') == u'10/11/09'
        assert i18n.format_date(value, format='medium') == u'10/11/2009'
        assert i18n.format_date(value, format='long') == u'10 de novembro de 2009'
        assert i18n.format_date(value, format='full') == u'terça-feira, 10 de novembro de 2009'

    def test_format_datetime(self):
        app = tipfy.WSGIApplication({'tipfy.ext.i18n': {'timezone': 'UTC'}})

        i18n.set_translations('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert i18n.format_datetime(value, format='short') == u'11/10/09 4:36 PM'
        assert i18n.format_datetime(value, format='medium') == u'Nov 10, 2009 4:36:05 PM'
        assert i18n.format_datetime(value, format='long') == u'November 10, 2009 4:36:05 PM +0000'
        assert i18n.format_datetime(value, format='full') == u'Tuesday, November 10, 2009 4:36:05 PM World (GMT) Time'

    def test_format_datetime_pt_BR(self):
        app = tipfy.WSGIApplication({'tipfy.ext.i18n': {'timezone': 'UTC'}})

        i18n.set_translations('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert i18n.format_datetime(value, format='short') == u'10/11/09 16:36'
        assert i18n.format_datetime(value, format='medium') == u'10/11/2009 16:36:05'
        assert i18n.format_datetime(value, format='long') == u'10 de novembro de 2009 16:36:05 +0000'
        assert i18n.format_datetime(value, format='full') == u'terça-feira, 10 de novembro de 2009 16h36min05s Horário Mundo (GMT)'

    def test_format_time(self):
        app = tipfy.WSGIApplication({'tipfy.ext.i18n': {'timezone': 'UTC'}})

        i18n.set_translations('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert i18n.format_time(value, format='short') == u'4:36 PM'
        assert i18n.format_time(value, format='medium') == u'4:36:05 PM'
        assert i18n.format_time(value, format='long') == u'4:36:05 PM +0000'
        assert i18n.format_time(value, format='full') == u'4:36:05 PM World (GMT) Time'

    def test_format_time_pt_BR(self):
        app = tipfy.WSGIApplication({'tipfy.ext.i18n': {'timezone': 'UTC'}})

        i18n.set_translations('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert i18n.format_time(value, format='short') == u'16:36'
        assert i18n.format_time(value, format='medium') == u'16:36:05'
        assert i18n.format_time(value, format='long') == u'16:36:05 +0000'
        assert i18n.format_time(value, format='full') == u'16h36min05s Horário Mundo (GMT)'

    #===========================================================================
    # Timezones
    #===========================================================================
    def test_default_get_tzinfo(self):
        app = tipfy.WSGIApplication({'tipfy.ext.i18n': {'timezone': 'UTC'}})
        assert i18n.get_tzinfo().zone == 'UTC'

        app.config.update('tipfy.ext.i18n', {'timezone': 'America/Chicago'})
        assert i18n.get_tzinfo().zone == 'America/Chicago'

        app.config.update('tipfy.ext.i18n', {'timezone': 'America/Sao_Paulo'})
        assert i18n.get_tzinfo().zone == 'America/Sao_Paulo'

    def test_get_tzinfo(self):
        tzinfo = i18n.get_tzinfo('UTC')
        assert tzinfo.zone == 'UTC'

        tzinfo = i18n.get_tzinfo('America/Chicago')
        assert tzinfo.zone == 'America/Chicago'

        tzinfo = i18n.get_tzinfo('America/Sao_Paulo')
        assert tzinfo.zone == 'America/Sao_Paulo'

    def test_to_local_timezone(self):
        app = tipfy.WSGIApplication({'tipfy.ext.i18n': {'timezone': 'US/Eastern'}})
        format = '%Y-%m-%d %H:%M:%S %Z%z'

        # Test datetime with timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0, tzinfo=i18n.pytz.UTC)
        localtime = i18n.to_local_timezone(base)
        result = localtime.strftime(format)
        assert result == '2002-10-27 01:00:00 EST-0500'

        # Test naive datetime - no timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0)
        localtime = i18n.to_local_timezone(base)
        result = localtime.strftime(format)
        assert result == '2002-10-27 01:00:00 EST-0500'

    def test_to_utc(self):
        app = tipfy.WSGIApplication({'tipfy.ext.i18n': {'timezone': 'US/Eastern'}})
        format = '%Y-%m-%d %H:%M:%S'

        # Test datetime with timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0, tzinfo=i18n.pytz.UTC)
        localtime = i18n.to_utc(base)
        result = localtime.strftime(format)

        assert result == '2002-10-27 06:00:00'

        # Test naive datetime - no timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0)
        localtime = i18n.to_utc(base)
        result = localtime.strftime(format)
        assert result == '2002-10-27 11:00:00'

    #===========================================================================
    # Number formatting
    #===========================================================================
    def test_format_number(self):
        app = tipfy.WSGIApplication()

        i18n.set_translations('en_US')
        assert i18n.format_number(1099) == u'1,099'

    def test_format_decimal(self):
        app = tipfy.WSGIApplication()

        i18n.set_translations('en_US')
        assert i18n.format_decimal(1.2345) == u'1.234'
        assert i18n.format_decimal(1.2346) == u'1.235'
        assert i18n.format_decimal(-1.2346) == u'-1.235'
        assert i18n.format_decimal(12345.5) == u'12,345.5'

        i18n.set_translations('sv_SE')
        assert i18n.format_decimal(1.2345) == u'1,234'

        i18n.set_translations('de')
        assert i18n.format_decimal(12345) == u'12.345'

    def test_format_currency(self):
        app = tipfy.WSGIApplication()

        i18n.set_translations('en_US')
        assert i18n.format_currency(1099.98, 'USD') == u'$1,099.98'
        assert i18n.format_currency(1099.98, 'EUR', u'\xa4\xa4 #,##0.00') == u'EUR 1,099.98'

        i18n.set_translations('es_CO')
        assert i18n.format_currency(1099.98, 'USD') == u'US$\xa01.099,98'

        i18n.set_translations('de_DE')
        assert i18n.format_currency(1099.98, 'EUR') == u'1.099,98\xa0\u20ac'

    def test_format_percent(self):
        app = tipfy.WSGIApplication()

        i18n.set_translations('en_US')
        assert i18n.format_percent(0.34) == u'34%'
        assert i18n.format_percent(25.1234) == u'2,512%'
        assert i18n.format_percent(25.1234, u'#,##0\u2030') == u'25,123\u2030'

        i18n.set_translations('sv_SE')
        assert i18n.format_percent(25.1234) == u'2\xa0512\xa0%'

    def test_format_scientific(self):
        app = tipfy.WSGIApplication()

        i18n.set_translations('en_US')
        assert i18n.format_scientific(10000) == u'1E4'
        assert i18n.format_scientific(1234567, u'##0E00') == u'1.23E06'

    def test_parse_number(self):
        app = tipfy.WSGIApplication()

        i18n.set_translations('en_US')
        assert i18n.parse_number('1,099') == 1099L

        i18n.set_translations('de_DE')
        assert i18n.parse_number('1.099') == 1099L

    @raises(NumberFormatError)
    def test_parse_number2(self):
        app = tipfy.WSGIApplication()

        i18n.set_translations('de')
        assert i18n.parse_number('1.099,98') == ''

    def test_parse_decimal(self):
        app = tipfy.WSGIApplication()

        i18n.set_translations('en_US')
        assert i18n.parse_decimal('1,099.98') == 1099.98

        i18n.set_translations('de')
        assert i18n.parse_decimal('1.099,98') == 1099.98

    @raises(NumberFormatError)
    def test_parse_decimal_error(self):
        app = tipfy.WSGIApplication()

        i18n.set_translations('de')
        assert i18n.parse_decimal('2,109,998') == ''
