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

from tipfy import Tipfy
from tipfy.ext.i18n import (_, format_currency, format_date, format_datetime,
    format_decimal, format_number, format_percent, format_scientific,
    format_time, gettext, get_locale, get_tzinfo, I18nMiddleware,
    is_default_locale, lazy_gettext, lazy_ngettext, ngettext, parse_number,
    parse_decimal, pytz, set_translations, set_translations_from_request,
    to_local_timezone, to_utc)


class Request(object):
    """A fake request object with GET, POST and cookies."""
    def __init__(self, args=None, form=None, cookies=None):
        self.args = args or {}
        self.form = form or {}
        self.cookies= cookies or {}
        self.context = {}


class Response(object):
    """A dummy response to test setting locale cookies."""
    def __init__(self):
        self.cookies = {}

    def set_cookie(self, name, value, **kwargs):
        self.cookies[name] = value


class TestI18nMiddleware(unittest.TestCase):
    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_post_dispatch(self):
        middleware = I18nMiddleware()

        app = Tipfy({
            'tipfy.ext.i18n': {
                'locale': 'jp_JP',
            },
        })
        request = Request()
        app.set_wsgi_app()
        app.set_request(request)

        response = Response()
        response = middleware.post_dispatch(None, response)
        assert isinstance(response, Response)
        assert response.cookies == {}

        request.context['locale'] = 'ru_RU'
        response = Response()
        response = middleware.post_dispatch(None, response)

        assert response.cookies == {'tipfy.locale': 'ru_RU'}
        assert isinstance(response, Response)

    def test_pre_dispatch_handler(self):
        app = Tipfy({
            'tipfy.ext.i18n': {
                'locale_request_lookup': [('args', 'language')],
            },
        })
        request = Request(args={'language': 'es_ES'})
        app.set_wsgi_app()
        app.set_request(request)

        middleware = I18nMiddleware()
        middleware.pre_dispatch_handler()
        assert request.context['locale'] == 'es_ES'

    def test_post_dispatch_handler(self):
        middleware = I18nMiddleware()

        app = Tipfy({
            'tipfy.ext.i18n': {
                'locale': 'jp_JP',
            },
        })
        request = Request()
        app.set_wsgi_app()
        app.set_request(request)

        response = Response()
        response = middleware.post_dispatch_handler(response)
        assert isinstance(response, Response)
        assert response.cookies == {}

        request.context['locale'] = 'ru_RU'
        response = Response()
        response = middleware.post_dispatch_handler(response)
        assert response.cookies == {'tipfy.locale': 'ru_RU'}
        assert isinstance(response, Response)


class TestI18n(unittest.TestCase):
    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    #===========================================================================
    # Translations
    #===========================================================================
    def test_set_translations(self):
        app = Tipfy()
        request = Request()
        app.set_wsgi_app()
        app.set_request(request)

        ctx = Tipfy.request.context
        assert ctx.get('locale', None) is None
        assert ctx.get('translations', None) is None

        set_translations('pt_BR')
        assert ctx['locale'] == 'pt_BR'
        assert isinstance(ctx['translations'], gettext_stdlib.NullTranslations)

    def test_set_translations_from_request(self):
        app = Tipfy({
            'tipfy.ext.i18n': {
                'locale': 'jp_JP',
            },
        })
        request = Request()
        app.set_wsgi_app()
        app.set_request(request)

        set_translations_from_request()
        assert request.context['locale'] == 'jp_JP'

    def test_set_translations_from_request_args(self):
        app = Tipfy({
            'tipfy.ext.i18n': {
                'locale_request_lookup': [('args', 'language')],
            },
        })
        request = Request(args={'language': 'es_ES'})
        app.set_wsgi_app()
        app.set_request(request)

        set_translations_from_request()
        assert request.context['locale'] == 'es_ES'

    def test_set_translations_from_request_form(self):
        app = Tipfy({
            'tipfy.ext.i18n': {
                'locale_request_lookup': [('form', 'language')],
            },
        })
        request = Request(form={'language': 'es_ES'})
        app.set_wsgi_app()
        app.set_request(request)

        set_translations_from_request()
        assert request.context['locale'] == 'es_ES'

    def test_set_translations_from_request_cookies(self):
        app = Tipfy({
            'tipfy.ext.i18n': {
                'locale_request_lookup': [('cookies', 'language')],
            },
        })
        request = Request(cookies={'language': 'es_ES'})
        app.set_wsgi_app()
        app.set_request(request)

        set_translations_from_request()
        assert request.context['locale'] == 'es_ES'

    def test_set_translations_from_request_args_form_cookies(self):
        app = Tipfy({
            'tipfy.ext.i18n': {
                'locale_request_lookup': [('args', 'foo'), ('form', 'bar'), ('cookies', 'language')],
            },
        })
        request = Request(cookies={'language': 'es_ES'})
        app.set_wsgi_app()
        app.set_request(request)

        set_translations_from_request()
        assert request.context['locale'] == 'es_ES'

    def test_set_translations_from_rule_args(self):
        app = Tipfy({
            'tipfy.ext.i18n': {
                'locale_request_lookup': [('rule_args', 'locale'),],
            },
        })
        request = Request()
        app.set_wsgi_app()
        app.set_request(request)

        request.rule_args = {'locale': 'es_ES'}
        set_translations_from_request()
        assert request.context['locale'] == 'es_ES'

        request.rule_args = {'locale': 'pt_BR'}
        set_translations_from_request()
        assert request.context['locale'] == 'pt_BR'

    def test_is_default_locale(self):
        app = Tipfy()
        request = Request()
        app.set_wsgi_app()
        app.set_request(request)

        request.context['locale'] = 'en_US'
        assert is_default_locale() is True
        request.context['locale'] = 'pt_BR'
        assert is_default_locale() is False

        app = Tipfy({'tipfy.ext.i18n': {'locale': 'pt_BR'}})
        request.context['locale'] = 'en_US'
        assert is_default_locale() is False
        request.context['locale'] = 'pt_BR'
        assert is_default_locale() is True


    def test_get_locale(self):
        app = Tipfy({
            'tipfy.ext.i18n': {
                'locale_request_lookup': [('args', 'foo'), ('form', 'bar'), ('cookies', 'language')],
            },
        })
        request = Request(cookies={'language': 'es_ES'})
        app.set_wsgi_app()
        app.set_request(request)

        assert get_locale() == 'es_ES'

    def test_get_locale_without_request(self):
        app = Tipfy()
        request = Request()
        app.set_wsgi_app()
        app.set_request(request)

        assert get_locale() == 'en_US'

#===========================================================================
# _(), gettext(), ngettext(), lazy_gettext(), lazy_ngettext()
#===========================================================================
class TestGettext(unittest.TestCase):
    def setUp(self):
        app = Tipfy()
        request = Request()
        app.set_wsgi_app()
        app.set_request(request)

    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    @raises(AttributeError)
    def test_translations_not_set(self):
        Tipfy.app = None
        Tipfy.request = None
        gettext('foo')

    def test_gettext(self):
        set_translations('en_US')
        assert gettext('foo') == u'foo'

    def test_gettext_(self):
        set_translations('en_US')
        assert _('foo') == u'foo'

    def test_ngettext(self):
        set_translations('en_US')
        assert ngettext('One foo', 'Many foos', 1) == u'One foo'
        assert ngettext('One foo', 'Many foos', 2) == u'Many foos'

    def test_lazy_gettext(self):
        set_translations('en_US')
        assert lazy_gettext('foo') == u'foo'

    def test_lazy_ngettext(self):
        set_translations('en_US')
        assert lazy_ngettext('One foo', 'Many foos', 1) == u'One foo'
        assert lazy_ngettext('One foo', 'Many foos', 2) == u'Many foos'

#===========================================================================
# Date formatting
#===========================================================================
class TestTimezones(unittest.TestCase):
    def setUp(self):
        app = Tipfy({'tipfy.ext.i18n': {'timezone': 'UTC'}})
        request = Request()
        app.set_wsgi_app()
        app.set_request(request)

    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_format_date(self):
        set_translations('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert format_date(value, format='short') == u'11/10/09'
        assert format_date(value, format='medium') == u'Nov 10, 2009'
        assert format_date(value, format='long') == u'November 10, 2009'
        assert format_date(value, format='full') == u'Tuesday, November 10, 2009'

    def test_format_date_pt_BR(self):
        set_translations('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert format_date(value, format='short') == u'10/11/09'
        assert format_date(value, format='medium') == u'10/11/2009'
        assert format_date(value, format='long') == u'10 de novembro de 2009'
        assert format_date(value, format='full') == u'terça-feira, 10 de novembro de 2009'

    def test_format_datetime(self):
        set_translations('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert format_datetime(value, format='short') == u'11/10/09 4:36 PM'
        assert format_datetime(value, format='medium') == u'Nov 10, 2009 4:36:05 PM'
        assert format_datetime(value, format='long') == u'November 10, 2009 4:36:05 PM +0000'
        assert format_datetime(value, format='full') == u'Tuesday, November 10, 2009 4:36:05 PM World (GMT) Time'

    def test_format_datetime_pt_BR(self):
        set_translations('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert format_datetime(value, format='short') == u'10/11/09 16:36'
        assert format_datetime(value, format='medium') == u'10/11/2009 16:36:05'
        assert format_datetime(value, format='long') == u'10 de novembro de 2009 16:36:05 +0000'
        assert format_datetime(value, format='full') == u'terça-feira, 10 de novembro de 2009 16h36min05s Horário Mundo (GMT)'

    def test_format_time(self):
        set_translations('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert format_time(value, format='short') == u'4:36 PM'
        assert format_time(value, format='medium') == u'4:36:05 PM'
        assert format_time(value, format='long') == u'4:36:05 PM +0000'
        assert format_time(value, format='full') == u'4:36:05 PM World (GMT) Time'

    def test_format_time_pt_BR(self):
        set_translations('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert format_time(value, format='short') == u'16:36'
        assert format_time(value, format='medium') == u'16:36:05'
        assert format_time(value, format='long') == u'16:36:05 +0000'
        assert format_time(value, format='full') == u'16h36min05s Horário Mundo (GMT)'

#===========================================================================
# Timezones
#===========================================================================
class TestTimezones(unittest.TestCase):
    def setUp(self):
        app = Tipfy()
        request = Request()
        app.set_wsgi_app()
        app.set_request(request)

    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_default_get_tzinfo(self):
        Tipfy.app.config.update('tipfy.ext.i18n', {'timezone': 'UTC'})

        assert get_tzinfo().zone == 'UTC'

        Tipfy.app.config.update('tipfy.ext.i18n', {'timezone': 'America/Chicago'})
        assert get_tzinfo().zone == 'America/Chicago'

        Tipfy.app.config.update('tipfy.ext.i18n', {'timezone': 'America/Sao_Paulo'})
        assert get_tzinfo().zone == 'America/Sao_Paulo'

    def test_get_tzinfo(self):
        tzinfo = get_tzinfo('UTC')
        assert tzinfo.zone == 'UTC'

        tzinfo = get_tzinfo('America/Chicago')
        assert tzinfo.zone == 'America/Chicago'

        tzinfo = get_tzinfo('America/Sao_Paulo')
        assert tzinfo.zone == 'America/Sao_Paulo'

    def test_to_local_timezone(self):
        Tipfy.app.config.update('tipfy.ext.i18n', {'timezone': 'US/Eastern'})

        format = '%Y-%m-%d %H:%M:%S %Z%z'

        # Test datetime with timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0, tzinfo=pytz.UTC)
        localtime = to_local_timezone(base)
        result = localtime.strftime(format)
        assert result == '2002-10-27 01:00:00 EST-0500'

        # Test naive datetime - no timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0)
        localtime = to_local_timezone(base)
        result = localtime.strftime(format)
        assert result == '2002-10-27 01:00:00 EST-0500'

    def test_to_utc(self):
        Tipfy.app.config.update('tipfy.ext.i18n', {'timezone': 'US/Eastern'})

        format = '%Y-%m-%d %H:%M:%S'

        # Test datetime with timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0, tzinfo=pytz.UTC)
        localtime = to_utc(base)
        result = localtime.strftime(format)

        assert result == '2002-10-27 06:00:00'

        # Test naive datetime - no timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0)
        localtime = to_utc(base)
        result = localtime.strftime(format)
        assert result == '2002-10-27 11:00:00'

#===========================================================================
# Number formatting
#===========================================================================
class TestNumberFormatting(unittest.TestCase):
    def setUp(self):
        app = Tipfy()
        request = Request()
        app.set_wsgi_app()
        app.set_request(request)

    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_format_number(self):
        set_translations('en_US')
        assert format_number(1099) == u'1,099'

    def test_format_decimal(self):
        set_translations('en_US')
        assert format_decimal(1.2345) == u'1.234'
        assert format_decimal(1.2346) == u'1.235'
        assert format_decimal(-1.2346) == u'-1.235'
        assert format_decimal(12345.5) == u'12,345.5'

        set_translations('sv_SE')
        assert format_decimal(1.2345) == u'1,234'

        set_translations('de')
        assert format_decimal(12345) == u'12.345'

    def test_format_currency(self):
        set_translations('en_US')
        assert format_currency(1099.98, 'USD') == u'$1,099.98'
        assert format_currency(1099.98, 'EUR', u'\xa4\xa4 #,##0.00') == u'EUR 1,099.98'

        set_translations('es_CO')
        assert format_currency(1099.98, 'USD') == u'US$\xa01.099,98'

        set_translations('de_DE')
        assert format_currency(1099.98, 'EUR') == u'1.099,98\xa0\u20ac'

    def test_format_percent(self):
        set_translations('en_US')
        assert format_percent(0.34) == u'34%'
        assert format_percent(25.1234) == u'2,512%'
        assert format_percent(25.1234, u'#,##0\u2030') == u'25,123\u2030'

        set_translations('sv_SE')
        assert format_percent(25.1234) == u'2\xa0512\xa0%'

    def test_format_scientific(self):
        set_translations('en_US')
        assert format_scientific(10000) == u'1E4'
        assert format_scientific(1234567, u'##0E00') == u'1.23E06'

    def test_parse_number(self):
        set_translations('en_US')
        assert parse_number('1,099') == 1099L

        set_translations('de_DE')
        assert parse_number('1.099') == 1099L

    @raises(NumberFormatError)
    def test_parse_number2(self):
        set_translations('de')
        assert parse_number('1.099,98') == ''

    def test_parse_decimal(self):
        set_translations('en_US')
        assert parse_decimal('1,099.98') == 1099.98

        set_translations('de')
        assert parse_decimal('1.099,98') == 1099.98

    @raises(NumberFormatError)
    def test_parse_decimal_error(self):
        set_translations('de')
        assert parse_decimal('2,109,998') == ''
