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
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

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
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_translations_not_set(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass
        self.assertRaises(AttributeError, i18n.gettext, 'foo')

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
        try:
            Tipfy.app.clear_locals()
        except:
            pass

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

    def test_set_translations_from_rule_args(self):
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
        try:
            Tipfy.app.clear_locals()
        except:
            pass

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

    """
    def test_parse_date(self):
       self.assertEqual(parse_date('4/1/04', locale='en_US'), datetime.date(2004, 4, 1))
       self.assertEqual(parse_date('01.04.2004', locale='de_DE'), datetime.date(2004, 4, 1))

    def test_parse_datetime(self):
       self.assertRaises(NotImplementedError, parse_datetime, '4/1/04 16:08:09', locale='en_US')

    def test_parse_time(self):
        self.assertEqual(parse_time('18:08:09', locale='en_US'), datetime.time(18, 8, 9))
        self.assertEqual(parse_time('18:08:09', locale='de_DE'), datetime.time(18, 8, 9))
    """

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
        try:
            Tipfy.app.clear_locals()
        except:
            pass

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

    """
    def test_get_timezone_location(self):
        self.assertEqual(get_timezone_location(get_timezone('America/St_Johns'), locale='de_DE'), u'Kanada (St. John\'s)')
        self.assertEqual(get_timezone_location(get_timezone('America/Mexico_City'), locale='de_DE'), u'Mexiko (Mexiko-Stadt)')
        self.assertEqual(get_timezone_location(get_timezone('Europe/Berlin'), locale='de_DE'), u'Deutschland')
    """
