# -*- coding: utf-8 -*-
"""
    Tests for tipfyext.i18n
"""
import datetime
import gettext as gettext_stdlib
import os
import unittest

from babel.numbers import NumberFormatError

from tipfy import Tipfy, RequestHandler, Response as BaseResponse, Rule
from tipfyext.i18n import (_, format_currency, format_date, format_datetime,
    format_decimal, format_number, format_percent, format_scientific,
    format_time, gettext, get_locale, get_translations, get_tzinfo,
    I18nMiddleware, is_default_locale, lazy_gettext, lazy_ngettext,
    list_translations, ngettext, parse_date, parse_datetime, parse_number,
    parse_decimal, parse_time, pytz, set_translations,
    set_translations_from_request, to_local_timezone, to_utc,
    get_timezone, get_timezone_location)


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
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_middleware_multiple_changes(self):
        class MyHandler(RequestHandler):
            middleware = [I18nMiddleware()]

            def get(self, **kwargs):
                locale = get_locale()
                return BaseResponse(locale)
                #return BaseResponse(str(self.request.cookies.get('locale')))

        app = Tipfy(rules=[
            Rule('/', name='home', handler=MyHandler)
        ], debug=True)

        client = app.get_test_client()
        response = client.get('/')
        self.assertEqual(response.data, 'en_US')

        response = client.get('/?lang=pt_BR', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'pt_BR')

        #self.assertEqual(str(response.headers.getlist('Set-Cookie')), None)
        response = client.get('/', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'pt_BR')

        response = client.get('/?lang=en_US', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'en_US')

#============================================================================
# Translations
#============================================================================
class TestTranslations(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_list_translations(self):
        cwd = os.getcwd()
        os.chdir(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources'))

        translations = list_translations()

        self.assertEqual(len(translations), 2)
        self.assertEqual(translations[0].language, 'en')
        self.assertEqual(translations[0].territory, 'US')
        self.assertEqual(translations[1].language, 'pt')
        self.assertEqual(translations[1].territory, 'BR')

        os.chdir(cwd)

    def test_list_translations_no_locale_dir(self):
        cwd = os.getcwd()
        os.chdir(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', 'locale'))

        self.assertEqual(list_translations(), [])

        os.chdir(cwd)

    def test_get_translations(self):
        app = Tipfy()
        request = Request()
        app.set_locals(request)

        ctx = request.context

        self.assertEqual(ctx.get('locale', None), None)
        self.assertEqual(ctx.get('translations', None), None)

        t = get_translations()

        self.assertNotEqual(ctx.get('locale', None), None)
        self.assertNotEqual(ctx.get('translations', None), None)

    def test_set_translations(self):
        app = Tipfy()
        request = Request()
        app.set_locals(request)

        ctx = Tipfy.request.context
        self.assertEqual(ctx.get('locale', None), None)
        self.assertEqual(ctx.get('translations', None), None)

        set_translations('pt_BR')
        self.assertEqual(ctx['locale'], 'pt_BR')
        self.assertEqual(isinstance(ctx['translations'], gettext_stdlib.NullTranslations), True)

    def test_set_translations_from_request(self):
        app = Tipfy(config={
            'tipfyext.i18n': {
                'locale': 'jp_JP',
            },
        })
        request = Request()
        app.set_locals(request)

        set_translations_from_request()
        self.assertEqual(request.context['locale'], 'jp_JP')

    def test_set_translations_from_request_args(self):
        app = Tipfy(config={
            'tipfyext.i18n': {
                'locale_request_lookup': [('args', 'language')],
            },
        })
        request = Request(args={'language': 'es_ES'})
        app.set_locals(request)

        set_translations_from_request()
        self.assertEqual(request.context['locale'], 'es_ES')

    def test_set_translations_from_request_form(self):
        app = Tipfy(config={
            'tipfyext.i18n': {
                'locale_request_lookup': [('form', 'language')],
            },
        })
        request = Request(form={'language': 'es_ES'})
        app.set_locals(request)

        set_translations_from_request()
        self.assertEqual(request.context['locale'], 'es_ES')

    def test_set_translations_from_request_cookies(self):
        app = Tipfy(config={
            'tipfyext.i18n': {
                'locale_request_lookup': [('cookies', 'language')],
            },
        })
        request = Request(cookies={'language': 'es_ES'})
        app.set_locals(request)

        set_translations_from_request()
        self.assertEqual(request.context['locale'], 'es_ES')

    def test_set_translations_from_request_args_form_cookies(self):
        app = Tipfy(config={
            'tipfyext.i18n': {
                'locale_request_lookup': [('args', 'foo'), ('form', 'bar'),
                ('cookies', 'language')],
            },
        })
        request = Request(cookies={'language': 'es_ES'})
        app.set_locals(request)

        set_translations_from_request()
        self.assertEqual(request.context['locale'], 'es_ES')

    def test_set_translations_from_rule_args(self):
        app = Tipfy(config={
            'tipfyext.i18n': {
                'locale_request_lookup': [('rule_args', 'locale'),],
            },
        })
        request = Request()
        app.set_locals(request)

        request.rule_args = {'locale': 'es_ES'}
        set_translations_from_request()
        self.assertEqual(request.context['locale'], 'es_ES')

        request.rule_args = {'locale': 'pt_BR'}
        set_translations_from_request()
        self.assertEqual(request.context['locale'], 'pt_BR')

    def test_is_default_locale(self):
        app = Tipfy()
        request = Request()
        app.set_locals(request)

        request.context['locale'] = 'en_US'
        self.assertEqual(is_default_locale(), True)
        request.context['locale'] = 'pt_BR'
        self.assertEqual(is_default_locale(), False)

        app = Tipfy(config={'tipfyext.i18n': {'locale': 'pt_BR'}})
        app.set_locals(request)

        request.context['locale'] = 'en_US'
        self.assertEqual(is_default_locale(), False)
        request.context['locale'] = 'pt_BR'
        self.assertEqual(is_default_locale(), True)


    def test_get_locale(self):
        app = Tipfy(config={
            'tipfyext.i18n': {
                'locale_request_lookup': [('args', 'foo'), ('form', 'bar'),
                ('cookies', 'language')],
            },
        })
        request = Request(cookies={'language': 'es_ES'})
        app.set_locals(request)

        self.assertEqual(get_locale(), 'es_ES')

    def test_get_locale_without_request(self):
        app = Tipfy()
        request = Request()
        app.set_locals(request)

        self.assertEqual(get_locale(), 'en_US')

#============================================================================
# _(), gettext(), ngettext(), lazy_gettext(), lazy_ngettext()
#============================================================================
class TestGettext(unittest.TestCase):
    def setUp(self):
        app = Tipfy()
        request = Request()
        app.set_locals(request)

    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_translations_not_set(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass
        self.assertRaises(RuntimeError, gettext, 'foo')

    def test_gettext(self):
        set_translations('en_US')
        self.assertEqual(gettext('foo'), u'foo')

    def test_gettext_(self):
        set_translations('en_US')
        self.assertEqual(_('foo'), u'foo')

    def test_ngettext(self):
        set_translations('en_US')
        self.assertEqual(ngettext('One foo', 'Many foos', 1), u'One foo')
        self.assertEqual(ngettext('One foo', 'Many foos', 2), u'Many foos')

    def test_lazy_gettext(self):
        set_translations('en_US')
        self.assertEqual(lazy_gettext('foo'), u'foo')

    def test_lazy_ngettext(self):
        set_translations('en_US')
        self.assertEqual(lazy_ngettext('One foo', 'Many foos', 1), u'One foo')
        self.assertEqual(lazy_ngettext('One foo', 'Many foos', 2), u'Many foos')

#============================================================================
# Date formatting
#============================================================================
class TestDates(unittest.TestCase):
    def setUp(self):
        app = Tipfy(config={'tipfyext.i18n': {'timezone': 'UTC'}})
        request = Request()
        app.set_locals(request)

    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_format_date(self):
        set_translations('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(format_date(value, format='short'), u'11/10/09')
        self.assertEqual(format_date(value, format='medium'), u'Nov 10, 2009')
        self.assertEqual(format_date(value, format='long'), u'November 10, 2009')
        self.assertEqual(format_date(value, format='full'), u'Tuesday, November 10, 2009')

    def test_format_date_no_format(self):
        set_translations('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)
        self.assertEqual(format_date(value), u'Nov 10, 2009')

    def test_format_date_no_format_but_configured(self):
        app = Tipfy(config={'tipfyext.i18n': {'timezone': 'UTC', 'date_formats': {
            'time':             'medium',
            'date':             'medium',
            'datetime':         'medium',
            'time.short':       None,
            'time.medium':      None,
            'time.full':        None,
            'time.long':        None,
            'date.short':       None,
            'date.medium':      'full',
            'date.full':        None,
            'date.long':        None,
            'datetime.short':   None,
            'datetime.medium':  None,
            'datetime.full':    None,
            'datetime.long':    None,
        }}})
        request = Request()
        app.set_locals(request)

        set_translations('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)
        self.assertEqual(format_date(value), u'Tuesday, November 10, 2009')

    def test_format_date_pt_BR(self):
        set_translations('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(format_date(value, format='short'), u'10/11/09')
        self.assertEqual(format_date(value, format='medium'), u'10/11/2009')
        self.assertEqual(format_date(value, format='long'), u'10 de novembro de 2009')
        self.assertEqual(format_date(value, format='full'), u'terça-feira, 10 de novembro de 2009')

    def test_format_datetime(self):
        set_translations('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(format_datetime(value, format='short'), u'11/10/09 4:36 PM')
        self.assertEqual(format_datetime(value, format='medium'), u'Nov 10, 2009 4:36:05 PM')
        self.assertEqual(format_datetime(value, format='long'), u'November 10, 2009 4:36:05 PM +0000')
        self.assertEqual(format_datetime(value, format='full'), u'Tuesday, November 10, 2009 4:36:05 PM World (GMT) Time')

    def test_format_datetime_no_format(self):
        set_translations('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)
        self.assertEqual(format_datetime(value), u'Nov 10, 2009 4:36:05 PM')

    def test_format_datetime_pt_BR(self):
        set_translations('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(format_datetime(value, format='short'), u'10/11/09 16:36')
        self.assertEqual(format_datetime(value, format='medium'), u'10/11/2009 16:36:05')
        self.assertEqual(format_datetime(value, format='long'), u'10 de novembro de 2009 16:36:05 +0000')
        self.assertEqual(format_datetime(value, format='full'), u'terça-feira, 10 de novembro de 2009 16h36min05s Horário Mundo (GMT)')

    def test_format_time(self):
        set_translations('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(format_time(value, format='short'), u'4:36 PM')
        self.assertEqual(format_time(value, format='medium'), u'4:36:05 PM')
        self.assertEqual(format_time(value, format='long'), u'4:36:05 PM +0000')
        self.assertEqual(format_time(value, format='full'), u'4:36:05 PM World (GMT) Time')

    def test_format_time_no_format(self):
        set_translations('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)
        self.assertEqual(format_time(value), u'4:36:05 PM')

    def test_format_time_pt_BR(self):
        set_translations('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(format_time(value, format='short'), u'16:36')
        self.assertEqual(format_time(value, format='medium'), u'16:36:05')
        self.assertEqual(format_time(value, format='long'), u'16:36:05 +0000')
        self.assertEqual(format_time(value, format='full'), u'16h36min05s Horário Mundo (GMT)')

    def test_parse_date(self):
       self.assertEqual(parse_date('4/1/04', locale='en_US'), datetime.date(2004, 4, 1))
       self.assertEqual(parse_date('01.04.2004', locale='de_DE'), datetime.date(2004, 4, 1))

    def test_parse_datetime(self):
       self.assertRaises(NotImplementedError, parse_datetime, '4/1/04 16:08:09', locale='en_US')

    def test_parse_time(self):
        self.assertEqual(parse_time('18:08:09', locale='en_US'), datetime.time(18, 8, 9))
        self.assertEqual(parse_time('18:08:09', locale='de_DE'), datetime.time(18, 8, 9))

#============================================================================
# Timezones
#============================================================================
class TestTimezones(unittest.TestCase):
    def setUp(self):
        app = Tipfy()
        request = Request()
        app.set_locals(request)

    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_default_get_tzinfo(self):
        Tipfy.app.config.update('tipfyext.i18n', {'timezone': 'UTC'})

        self.assertEqual(get_tzinfo().zone, 'UTC')

        Tipfy.app.config.update('tipfyext.i18n', {'timezone': 'America/Chicago'})
        self.assertEqual(get_tzinfo().zone, 'America/Chicago')

        Tipfy.app.config.update('tipfyext.i18n', {'timezone': 'America/Sao_Paulo'})
        self.assertEqual(get_tzinfo().zone, 'America/Sao_Paulo')

    def test_get_tzinfo(self):
        tzinfo = get_tzinfo('UTC')
        self.assertEqual(tzinfo.zone, 'UTC')

        tzinfo = get_tzinfo('America/Chicago')
        self.assertEqual(tzinfo.zone, 'America/Chicago')

        tzinfo = get_tzinfo('America/Sao_Paulo')
        self.assertEqual(tzinfo.zone, 'America/Sao_Paulo')

    def test_to_local_timezone(self):
        Tipfy.app.config.update('tipfyext.i18n', {'timezone': 'US/Eastern'})

        format = '%Y-%m-%d %H:%M:%S %Z%z'

        # Test datetime with timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0, tzinfo=pytz.UTC)
        localtime = to_local_timezone(base)
        result = localtime.strftime(format)
        self.assertEqual(result, '2002-10-27 01:00:00 EST-0500')

        # Test naive datetime - no timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0)
        localtime = to_local_timezone(base)
        result = localtime.strftime(format)
        self.assertEqual(result, '2002-10-27 01:00:00 EST-0500')

    def test_to_utc(self):
        Tipfy.app.config.update('tipfyext.i18n', {'timezone': 'US/Eastern'})

        format = '%Y-%m-%d %H:%M:%S'

        # Test datetime with timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0, tzinfo=pytz.UTC)
        localtime = to_utc(base)
        result = localtime.strftime(format)

        self.assertEqual(result, '2002-10-27 06:00:00')

        # Test naive datetime - no timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0)
        localtime = to_utc(base)
        result = localtime.strftime(format)
        self.assertEqual(result, '2002-10-27 11:00:00')

    def test_get_timezone_location(self):
        self.assertEqual(get_timezone_location(get_timezone('America/St_Johns'), locale='de_DE'), u'Kanada (St. John\'s)')
        self.assertEqual(get_timezone_location(get_timezone('America/Mexico_City'), locale='de_DE'), u'Mexiko (Mexiko-Stadt)')
        self.assertEqual(get_timezone_location(get_timezone('Europe/Berlin'), locale='de_DE'), u'Deutschland')

#============================================================================
# Number formatting
#============================================================================
class TestNumberFormatting(unittest.TestCase):
    def setUp(self):
        app = Tipfy()
        request = Request()
        app.set_locals(request)

    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_format_number(self):
        set_translations('en_US')
        self.assertEqual(format_number(1099), u'1,099')

    def test_format_decimal(self):
        set_translations('en_US')
        self.assertEqual(format_decimal(1.2345), u'1.234')
        self.assertEqual(format_decimal(1.2346), u'1.235')
        self.assertEqual(format_decimal(-1.2346), u'-1.235')
        self.assertEqual(format_decimal(12345.5), u'12,345.5')

        set_translations('sv_SE')
        self.assertEqual(format_decimal(1.2345), u'1,234')

        set_translations('de')
        self.assertEqual(format_decimal(12345), u'12.345')

    def test_format_currency(self):
        set_translations('en_US')
        self.assertEqual(format_currency(1099.98, 'USD'), u'$1,099.98')
        self.assertEqual(format_currency(1099.98, 'EUR', u'\xa4\xa4 #,##0.00'), u'EUR 1,099.98')

        set_translations('es_CO')
        self.assertEqual(format_currency(1099.98, 'USD'), u'US$\xa01.099,98')

        set_translations('de_DE')
        self.assertEqual(format_currency(1099.98, 'EUR'), u'1.099,98\xa0\u20ac')

    def test_format_percent(self):
        set_translations('en_US')
        self.assertEqual(format_percent(0.34), u'34%')
        self.assertEqual(format_percent(25.1234), u'2,512%')
        self.assertEqual(format_percent(25.1234, u'#,##0\u2030'), u'25,123\u2030')

        set_translations('sv_SE')
        self.assertEqual(format_percent(25.1234), u'2\xa0512\xa0%')

    def test_format_scientific(self):
        set_translations('en_US')
        self.assertEqual(format_scientific(10000), u'1E4')
        self.assertEqual(format_scientific(1234567, u'##0E00'), u'1.23E06')

    def test_parse_number(self):
        set_translations('en_US')
        self.assertEqual(parse_number('1,099'), 1099L)

        set_translations('de_DE')
        self.assertEqual(parse_number('1.099'), 1099L)

    def test_parse_number2(self):
        set_translations('de')
        self.assertRaises(NumberFormatError, parse_number, '1.099,98')

    def test_parse_decimal(self):
        set_translations('en_US')
        self.assertEqual(parse_decimal('1,099.98'), 1099.98)

        set_translations('de')
        self.assertEqual(parse_decimal('1.099,98'), 1099.98)

    def test_parse_decimal_error(self):
        set_translations('de')
        self.assertRaises(NumberFormatError, parse_decimal, '2,109,998')
