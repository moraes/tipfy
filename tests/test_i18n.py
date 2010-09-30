# -*- coding: utf-8 -*-
"""
    Tests for tipfy.i18n
"""
import datetime
import gettext as gettext_stdlib
import os
import unittest

from babel.numbers import NumberFormatError

from pytz.gae import pytz

from tipfy import Tipfy, RequestHandler, Request, Response, Rule
import tipfy.i18n as i18n

#==============================================================================
# I18nMiddleware
#==============================================================================
class TestI18nMiddleware(unittest.TestCase):
    def test_middleware_multiple_changes(self):
        class MyHandler(RequestHandler):
            middleware = [i18n.I18nMiddleware()]

            def get(self, **kwargs):
                locale = self.request.i18n_store.locale
                return Response(locale)

        app = Tipfy(rules=[
            Rule('/', name='home', handler=MyHandler)
        ], config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
        })

        client = app.get_test_client()
        response = client.get('/')
        self.assertEqual(response.data, 'en_US')

        response = client.get('/?lang=pt_BR', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'pt_BR')

        response = client.get('/?lang=en_US', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'en_US')

#==============================================================================
# _(), gettext(), ngettext(), lazy_gettext(), lazy_ngettext()
#==============================================================================
class TestGettext(unittest.TestCase):
    def setUp(self):
        app = Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
            'tipfy.i18n': {
                'timezone': 'UTC'
            },
        })
        app.set_locals(Request.from_values('/'))

    def tearDown(self):
        Tipfy.app.clear_locals()

    '''
    def test_translations_not_set(self):
        Tipfy.app.clear_locals()
        self.assertRaises(AttributeError, i18n.gettext, 'foo')
    '''
    def test_gettext(self):
        self.assertEqual(i18n.gettext('foo'), u'foo')

    def test_gettext_(self):
        self.assertEqual(i18n._('foo'), u'foo')

    def test_ngettext(self):
        self.assertEqual(i18n.ngettext('One foo', 'Many foos', 1), u'One foo')
        self.assertEqual(i18n.ngettext('One foo', 'Many foos', 2), u'Many foos')

    def test_lazy_gettext(self):
        self.assertEqual(i18n.lazy_gettext('foo'), u'foo')

    def test_lazy_ngettext(self):
        self.assertEqual(i18n.lazy_ngettext('One foo', 'Many foos', 1), u'One foo')
        self.assertEqual(i18n.lazy_ngettext('One foo', 'Many foos', 2), u'Many foos')


#==============================================================================
# I18nStore.set_locale_for_request()
#==============================================================================
class TestLocaleForRequest(unittest.TestCase):
    def setUp(self):
        app = Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
            'tipfy.i18n': {
                'timezone': 'UTC'
            },
        })
        app.set_locals(Request.from_values('/'))

    def tearDown(self):
        Tipfy.app.clear_locals()

    def test_set_locale_for_request(self):
        Tipfy.app.config['tipfy.i18n']['locale'] = 'jp_JP'
        self.assertEqual(Tipfy.request.i18n_store.locale, 'jp_JP')

    def test_set_locale_for_request_args(self):
        Tipfy.app.config['tipfy.i18n']['locale_request_lookup'] = [('args', 'language')]
        Tipfy.app.set_locals(Request.from_values(query_string={'language': 'es_ES'}))
        self.assertEqual(Tipfy.request.i18n_store.locale, 'es_ES')

    def test_set_locale_for_request_form(self):
        Tipfy.app.config['tipfy.i18n']['locale_request_lookup'] = [('form', 'language')]
        Tipfy.app.set_locals(Request.from_values(data={'language': 'es_ES'}, method='POST'))
        self.assertEqual(Tipfy.request.i18n_store.locale, 'es_ES')

    def test_set_locale_for_request_cookies(self):
        Tipfy.app.config['tipfy.i18n']['locale_request_lookup'] = [('cookies', 'language')]
        Tipfy.app.set_locals(Request.from_values(headers=[('Cookie', 'language="es_ES"; Path=/')]))
        self.assertEqual(Tipfy.request.i18n_store.locale, 'es_ES')

    def test_set_locale_for_request_args_cookies(self):
        Tipfy.app.config['tipfy.i18n']['locale_request_lookup'] = [
            ('args', 'foo'),
            ('cookies', 'language')
        ]
        Tipfy.app.set_locals(Request.from_values(headers=[('Cookie', 'language="es_ES"; Path=/')]))
        self.assertEqual(Tipfy.request.i18n_store.locale, 'es_ES')

    def test_set_locale_from_rule_args(self):
        Tipfy.app.config['tipfy.i18n']['locale_request_lookup'] = [('rule_args', 'locale'),]
        request = Request.from_values('/')
        request.rule_args = {'locale': 'es_ES'}
        Tipfy.app.set_locals(request)
        self.assertEqual(Tipfy.request.i18n_store.locale, 'es_ES')

#==============================================================================
# Date formatting
#==============================================================================
class TestDates(unittest.TestCase):
    def setUp(self):
        app = Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
            'tipfy.i18n': {
                'timezone': 'UTC'
            },
        })
        app.set_locals(Request.from_values('/'))

    def tearDown(self):
        Tipfy.app.clear_locals()

    def test_format_date(self):
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(i18n.format_date(value, format='short'), u'11/10/09')
        self.assertEqual(i18n.format_date(value, format='medium'), u'Nov 10, 2009')
        self.assertEqual(i18n.format_date(value, format='long'), u'November 10, 2009')
        self.assertEqual(i18n.format_date(value, format='full'), u'Tuesday, November 10, 2009')

    def test_format_date_no_format(self):
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)
        self.assertEqual(i18n.format_date(value), u'Nov 10, 2009')

    def test_format_date_no_format_but_configured(self):
        app = Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
            'tipfy.i18n': {
                'timezone': 'UTC',
                'date_formats': {
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
                }
            }
        })
        app.set_locals(Request.from_values('/'))

        value = datetime.datetime(2009, 11, 10, 16, 36, 05)
        self.assertEqual(i18n.format_date(value), u'Tuesday, November 10, 2009')

    def test_format_date_pt_BR(self):
        i18n.set_locale('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(i18n.format_date(value, format='short'), u'10/11/09')
        self.assertEqual(i18n.format_date(value, format='medium'), u'10/11/2009')
        self.assertEqual(i18n.format_date(value, format='long'), u'10 de novembro de 2009')
        self.assertEqual(i18n.format_date(value, format='full'), u'terça-feira, 10 de novembro de 2009')

    def test_format_datetime(self):
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(i18n.format_datetime(value, format='short'), u'11/10/09 4:36 PM')
        self.assertEqual(i18n.format_datetime(value, format='medium'), u'Nov 10, 2009 4:36:05 PM')
        self.assertEqual(i18n.format_datetime(value, format='long'), u'November 10, 2009 4:36:05 PM +0000')
        self.assertEqual(i18n.format_datetime(value, format='full'), u'Tuesday, November 10, 2009 4:36:05 PM World (GMT) Time')

        self.assertEqual(i18n.format_datetime(value, format='short', timezone='America/Chicago'), u'11/10/09 10:36 AM')

    def test_format_datetime_no_format(self):
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)
        self.assertEqual(i18n.format_datetime(value), u'Nov 10, 2009 4:36:05 PM')

    def test_format_datetime_pt_BR(self):
        i18n.set_locale('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(i18n.format_datetime(value, format='short'), u'10/11/09 16:36')
        self.assertEqual(i18n.format_datetime(value, format='medium'), u'10/11/2009 16:36:05')
        self.assertEqual(i18n.format_datetime(value, format='long'), u'10 de novembro de 2009 16:36:05 +0000')
        self.assertEqual(i18n.format_datetime(value, format='full'), u'terça-feira, 10 de novembro de 2009 16h36min05s Horário Mundo (GMT)')

    def test_format_time(self):
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(i18n.format_time(value, format='short'), u'4:36 PM')
        self.assertEqual(i18n.format_time(value, format='medium'), u'4:36:05 PM')
        self.assertEqual(i18n.format_time(value, format='long'), u'4:36:05 PM +0000')
        self.assertEqual(i18n.format_time(value, format='full'), u'4:36:05 PM World (GMT) Time')

    def test_format_time_no_format(self):
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)
        self.assertEqual(i18n.format_time(value), u'4:36:05 PM')

    def test_format_time_pt_BR(self):
        i18n.set_locale('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(i18n.format_time(value, format='short'), u'16:36')
        self.assertEqual(i18n.format_time(value, format='medium'), u'16:36:05')
        self.assertEqual(i18n.format_time(value, format='long'), u'16:36:05 +0000')
        self.assertEqual(i18n.format_time(value, format='full'), u'16h36min05s Horário Mundo (GMT)')

        self.assertEqual(i18n.format_time(value, format='short', timezone='America/Chicago'), u'10:36')

    def test_parse_date(self):
       self.assertEqual(i18n.parse_date('4/1/04', locale='en_US'), datetime.date(2004, 4, 1))
       self.assertEqual(i18n.parse_date('01.04.2004', locale='de_DE'), datetime.date(2004, 4, 1))

    def test_parse_datetime(self):
       self.assertRaises(NotImplementedError, i18n.parse_datetime, '4/1/04 16:08:09', locale='en_US')

    def test_parse_time(self):
        self.assertEqual(i18n.parse_time('18:08:09', locale='en_US'), datetime.time(18, 8, 9))
        self.assertEqual(i18n.parse_time('18:08:09', locale='de_DE'), datetime.time(18, 8, 9))

    def test_format_timedelta(self):
        if not getattr(i18n, 'format_timedelta', None):
            return

        self.assertEqual(i18n.format_timedelta(datetime.timedelta(weeks=12), locale='en_US'), u'3 months')
        self.assertEqual(i18n.format_timedelta(datetime.timedelta(seconds=1), locale='es'), u'1 segundo')

        self.assertEqual(i18n.format_timedelta(datetime.timedelta(hours=3), granularity='day', locale='en_US'), u'1 day')

        self.assertEqual(i18n.format_timedelta(datetime.timedelta(hours=23), threshold=0.9, locale='en_US'), u'1 day')

        self.assertEqual(i18n.format_timedelta(datetime.timedelta(hours=23), threshold=1.1, locale='en_US'), u'23 hours')

        self.assertEqual(i18n.format_timedelta(datetime.datetime.now() - datetime.timedelta(days=5), threshold=1.1, locale='en_US'), u'5 days')


#==============================================================================
# Timezones
#==============================================================================
class TestTimezones(unittest.TestCase):
    def setUp(self):
        app = Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
            'tipfy.i18n': {
                'timezone': 'UTC'
            },
        })
        app.set_locals(Request.from_values('/'))

    def tearDown(self):
        Tipfy.app.clear_locals()

    def test_set_timezone(self):
        Tipfy.request.i18n_store.set_timezone('UTC')
        self.assertEqual(Tipfy.request.i18n_store.tzinfo.zone, 'UTC')

        Tipfy.request.i18n_store.set_timezone('America/Chicago')
        self.assertEqual(Tipfy.request.i18n_store.tzinfo.zone, 'America/Chicago')

        Tipfy.request.i18n_store.set_timezone('America/Sao_Paulo')
        self.assertEqual(Tipfy.request.i18n_store.tzinfo.zone, 'America/Sao_Paulo')

    def test_to_local_timezone(self):
        Tipfy.request.i18n_store.set_timezone('US/Eastern')

        format = '%Y-%m-%d %H:%M:%S %Z%z'

        # Test datetime with timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0, tzinfo=pytz.UTC)
        localtime = i18n.to_local_timezone(base)
        result = localtime.strftime(format)
        self.assertEqual(result, '2002-10-27 01:00:00 EST-0500')

        # Test naive datetime - no timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0)
        localtime = i18n.to_local_timezone(base)
        result = localtime.strftime(format)
        self.assertEqual(result, '2002-10-27 01:00:00 EST-0500')

    def test_to_utc(self):
        Tipfy.request.i18n_store.set_timezone('US/Eastern')

        format = '%Y-%m-%d %H:%M:%S'

        # Test datetime with timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0, tzinfo=pytz.UTC)
        localtime = i18n.to_utc(base)
        result = localtime.strftime(format)

        self.assertEqual(result, '2002-10-27 06:00:00')

        # Test naive datetime - no timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0)
        localtime = i18n.to_utc(base)
        result = localtime.strftime(format)
        self.assertEqual(result, '2002-10-27 11:00:00')

    def test_get_timezone_location(self):
        self.assertEqual(i18n.get_timezone_location(pytz.timezone('America/St_Johns'), locale='de_DE'), u'Kanada (St. John\'s)')
        self.assertEqual(i18n.get_timezone_location(pytz.timezone('America/Mexico_City'), locale='de_DE'), u'Mexiko (Mexiko-Stadt)')
        self.assertEqual(i18n.get_timezone_location(pytz.timezone('Europe/Berlin'), locale='de_DE'), u'Deutschland')


#==============================================================================
# Number formatting
#==============================================================================
class TestNumberFormatting(unittest.TestCase):
    def setUp(self):
        app = Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
            'tipfy.i18n': {
                'timezone': 'UTC'
            },
        })
        app.set_locals(Request.from_values('/'))

    def tearDown(self):
        Tipfy.app.clear_locals()

    def test_format_number(self):
        i18n.set_locale('en_US')
        self.assertEqual(i18n.format_number(1099), u'1,099')

    def test_format_decimal(self):
        i18n.set_locale('en_US')
        self.assertEqual(i18n.format_decimal(1.2345), u'1.234')
        self.assertEqual(i18n.format_decimal(1.2346), u'1.235')
        self.assertEqual(i18n.format_decimal(-1.2346), u'-1.235')
        self.assertEqual(i18n.format_decimal(12345.5), u'12,345.5')

        i18n.set_locale('sv_SE')
        self.assertEqual(i18n.format_decimal(1.2345), u'1,234')

        i18n.set_locale('de')
        self.assertEqual(i18n.format_decimal(12345), u'12.345')

    def test_format_currency(self):
        i18n.set_locale('en_US')
        self.assertEqual(i18n.format_currency(1099.98, 'USD'), u'$1,099.98')
        self.assertEqual(i18n.format_currency(1099.98, 'EUR', u'\xa4\xa4 #,##0.00'), u'EUR 1,099.98')

        i18n.set_locale('es_CO')
        self.assertEqual(i18n.format_currency(1099.98, 'USD'), u'US$\xa01.099,98')

        i18n.set_locale('de_DE')
        self.assertEqual(i18n.format_currency(1099.98, 'EUR'), u'1.099,98\xa0\u20ac')

    def test_format_percent(self):
        i18n.set_locale('en_US')
        self.assertEqual(i18n.format_percent(0.34), u'34%')
        self.assertEqual(i18n.format_percent(25.1234), u'2,512%')
        self.assertEqual(i18n.format_percent(25.1234, u'#,##0\u2030'), u'25,123\u2030')

        i18n.set_locale('sv_SE')
        self.assertEqual(i18n.format_percent(25.1234), u'2\xa0512\xa0%')

    def test_format_scientific(self):
        i18n.set_locale('en_US')
        self.assertEqual(i18n.format_scientific(10000), u'1E4')
        self.assertEqual(i18n.format_scientific(1234567, u'##0E00'), u'1.23E06')

    def test_parse_number(self):
        i18n.set_locale('en_US')
        self.assertEqual(i18n.parse_number('1,099'), 1099L)

        i18n.set_locale('de_DE')
        self.assertEqual(i18n.parse_number('1.099'), 1099L)

    def test_parse_number2(self):
        i18n.set_locale('de')
        self.assertRaises(NumberFormatError, i18n.parse_number, '1.099,98')

    def test_parse_decimal(self):
        i18n.set_locale('en_US')
        self.assertEqual(i18n.parse_decimal('1,099.98'), 1099.98)

        i18n.set_locale('de')
        self.assertEqual(i18n.parse_decimal('1.099,98'), 1099.98)

    def test_parse_decimal_error(self):
        i18n.set_locale('de')
        self.assertRaises(NumberFormatError, i18n.parse_decimal, '2,109,998')


#============================================================================
# Miscelaneous
#============================================================================
class TestMiscelaneous(unittest.TestCase):
    def setUp(self):
        app = Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
            'tipfy.i18n': {
                'timezone': 'UTC'
            },
        })
        app.set_locals(Request.from_values('/'))

    def tearDown(self):
        Tipfy.app.clear_locals()

    def test_list_translations(self):
        cwd = os.getcwd()
        os.chdir(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources'))

        translations = i18n.list_translations()

        self.assertEqual(len(translations), 2)
        self.assertEqual(translations[0].language, 'en')
        self.assertEqual(translations[0].territory, 'US')
        self.assertEqual(translations[1].language, 'pt')
        self.assertEqual(translations[1].territory, 'BR')

        os.chdir(cwd)

    def test_list_translations_no_locale_dir(self):
        cwd = os.getcwd()
        os.chdir(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', 'locale'))

        self.assertEqual(i18n.list_translations(), [])

        os.chdir(cwd)
