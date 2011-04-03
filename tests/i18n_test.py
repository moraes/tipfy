# -*- coding: utf-8 -*-
"""
    Tests for tipfy.i18n
"""
from __future__ import with_statement

import datetime
import gettext as gettext_stdlib
import os
import unittest

from babel.numbers import NumberFormatError

from pytz.gae import pytz

from tipfy.app import App, Request, Response
from tipfy.handler import RequestHandler
from tipfy.routing import Rule
from tipfy.local import local, get_request
from tipfy.sessions import SessionMiddleware
import tipfy.i18n as i18n

import test_utils


class BaseTestCase(test_utils.BaseTestCase):
    def setUp(self):
        app = App(rules=[
            Rule('/', name='home', handler=RequestHandler)
        ], config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
            'tipfy.i18n': {
                'timezone': 'UTC'
            },
        })
        local.request = request = Request.from_values('/')
        request.app = app
        test_utils.BaseTestCase.setUp(self)

    #==========================================================================
    # I18nMiddleware
    #==========================================================================

    def test_middleware_multiple_changes(self):
        class MyHandler(RequestHandler):
            middleware = [SessionMiddleware(), i18n.I18nMiddleware()]

            def get(self, **kwargs):
                locale = self.i18n.locale
                return Response(locale)

        app = App(rules=[
            Rule('/', name='home', handler=MyHandler)
        ], config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
            'tipfy.i18n': {
                'locale_request_lookup': [('args', 'lang'), ('session', '_locale')],
            }
        })

        client = app.get_test_client()
        response = client.get('/')
        self.assertEqual(response.data, 'en_US')

        response = client.get('/?lang=pt_BR')
        self.assertEqual(response.data, 'pt_BR')

        response = client.get('/')
        self.assertEqual(response.data, 'pt_BR')

        response = client.get('/?lang=en_US')
        self.assertEqual(response.data, 'en_US')

        response = client.get('/')
        self.assertEqual(response.data, 'en_US')

    #==========================================================================
    # _(), gettext(), ngettext(), lazy_gettext(), lazy_ngettext()
    #==========================================================================

    def test_translations_not_set(self):
        # We release it here because it is set on setUp()
        local.__release_local__()
        self.assertRaises(AttributeError, i18n.gettext, 'foo')

    def test_gettext(self):
        self.assertEqual(i18n.gettext('foo'), u'foo')

    def test_gettext_(self):
        self.assertEqual(i18n._('foo'), u'foo')

    def test_gettext_with_variables(self):
        self.assertEqual(i18n.gettext('foo %(foo)s'), u'foo %(foo)s')
        self.assertEqual(i18n.gettext('foo %(foo)s') % {'foo': 'bar'}, u'foo bar')
        self.assertEqual(i18n.gettext('foo %(foo)s', foo='bar'), u'foo bar')

    def test_ngettext(self):
        self.assertEqual(i18n.ngettext('One foo', 'Many foos', 1), u'One foo')
        self.assertEqual(i18n.ngettext('One foo', 'Many foos', 2), u'Many foos')

    def test_ngettext_with_variables(self):
        self.assertEqual(i18n.ngettext('One foo %(foo)s', 'Many foos %(foo)s', 1), u'One foo %(foo)s')
        self.assertEqual(i18n.ngettext('One foo %(foo)s', 'Many foos %(foo)s', 2), u'Many foos %(foo)s')
        self.assertEqual(i18n.ngettext('One foo %(foo)s', 'Many foos %(foo)s', 1, foo='bar'), u'One foo bar')
        self.assertEqual(i18n.ngettext('One foo %(foo)s', 'Many foos %(foo)s', 2, foo='bar'), u'Many foos bar')
        self.assertEqual(i18n.ngettext('One foo %(foo)s', 'Many foos %(foo)s', 1) % {'foo': 'bar'}, u'One foo bar')
        self.assertEqual(i18n.ngettext('One foo %(foo)s', 'Many foos %(foo)s', 2) % {'foo': 'bar'}, u'Many foos bar')

    def test_lazy_gettext(self):
        self.assertEqual(i18n.lazy_gettext('foo'), u'foo')

    def test_lazy_ngettext(self):
        self.assertEqual(i18n.lazy_ngettext('One foo', 'Many foos', 1), u'One foo')
        self.assertEqual(i18n.lazy_ngettext('One foo', 'Many foos', 2), u'Many foos')

    #==========================================================================
    # I18nStore.get_store_for_request()
    #==========================================================================

    def get_app(self):
        return App(rules=[
            Rule('/', name='home', handler=RequestHandler)
        ], config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
            'tipfy.i18n': {
                'timezone': 'UTC'
            },
        })

    def test_get_store_for_request(self):
        app = self.get_app()
        app.config['tipfy.i18n']['locale'] = 'jp_JP'

        with app.get_test_handler('/') as handler:
            self.assertEqual(handler.i18n.locale, 'jp_JP')

    def test_get_store_for_request_args(self):
        app = self.get_app()
        app.config['tipfy.i18n']['locale_request_lookup'] = [('args', 'language')]

        with app.get_test_handler('/', query_string={'language': 'es_ES'}) as handler:
            self.assertEqual(handler.i18n.locale, 'es_ES')

    def test_get_store_for_request_form(self):
        app = self.get_app()
        app.config['tipfy.i18n']['locale_request_lookup'] = [('form', 'language')]

        with app.get_test_handler('/', data={'language': 'es_ES'}, method='POST') as handler:
            self.assertEqual(handler.i18n.locale, 'es_ES')

    def test_get_store_for_request_cookies(self):
        app = self.get_app()
        app.config['tipfy.i18n']['locale_request_lookup'] = [('cookies', 'language')]

        with app.get_test_handler('/', headers=[('Cookie', 'language="es_ES"; Path=/')]) as handler:
            self.assertEqual(handler.i18n.locale, 'es_ES')

    def test_get_store_for_request_args_cookies(self):
        app = self.get_app()
        app.config['tipfy.i18n']['locale_request_lookup'] = [
            ('args', 'foo'),
            ('cookies', 'language')
        ]

        with app.get_test_handler('/', headers=[('Cookie', 'language="es_ES"; Path=/')]) as handler:
            self.assertEqual(handler.i18n.locale, 'es_ES')

    def test_get_store_for_request_rule_args(self):
        app = self.get_app()
        app.config['tipfy.i18n']['locale_request_lookup'] = [('rule_args', 'locale'),]

        with app.get_test_handler('/') as handler:
            handler.request.rule_args = {'locale': 'es_ES'}
            self.assertEqual(handler.i18n.locale, 'es_ES')

    #==========================================================================
    # Date formatting
    #==========================================================================

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
        app = App(config={
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
        local.request = request = Request.from_values('/')
        request.app = app

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
        #self.assertEqual(i18n.format_datetime(value, format='full'), u'Tuesday, November 10, 2009 4:36:05 PM World (GMT) Time')
        self.assertEqual(i18n.format_datetime(value, format='full'), u'Tuesday, November 10, 2009 4:36:05 PM GMT+00:00')

        i18n.set_timezone('America/Chicago')
        self.assertEqual(i18n.format_datetime(value, format='short'), u'11/10/09 10:36 AM')

    def test_format_datetime_no_format(self):
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)
        self.assertEqual(i18n.format_datetime(value), u'Nov 10, 2009 4:36:05 PM')

    def test_format_datetime_pt_BR(self):
        i18n.set_locale('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(i18n.format_datetime(value, format='short'), u'10/11/09 16:36')
        self.assertEqual(i18n.format_datetime(value, format='medium'), u'10/11/2009 16:36:05')
        #self.assertEqual(i18n.format_datetime(value, format='long'), u'10 de novembro de 2009 16:36:05 +0000')
        self.assertEqual(i18n.format_datetime(value, format='long'), u'10 de novembro de 2009 16h36min05s +0000')
        #self.assertEqual(i18n.format_datetime(value, format='full'), u'terça-feira, 10 de novembro de 2009 16h36min05s Horário Mundo (GMT)')
        self.assertEqual(i18n.format_datetime(value, format='full'), u'ter\xe7a-feira, 10 de novembro de 2009 16h36min05s GMT+00:00')

    def test_format_time(self):
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(i18n.format_time(value, format='short'), u'4:36 PM')
        self.assertEqual(i18n.format_time(value, format='medium'), u'4:36:05 PM')
        self.assertEqual(i18n.format_time(value, format='long'), u'4:36:05 PM +0000')
        #self.assertEqual(i18n.format_time(value, format='full'), u'4:36:05 PM World (GMT) Time')
        self.assertEqual(i18n.format_time(value, format='full'), u'4:36:05 PM GMT+00:00')

    def test_format_time_no_format(self):
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)
        self.assertEqual(i18n.format_time(value), u'4:36:05 PM')

    def test_format_time_pt_BR(self):
        i18n.set_locale('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(i18n.format_time(value, format='short'), u'16:36')
        self.assertEqual(i18n.format_time(value, format='medium'), u'16:36:05')
        #self.assertEqual(i18n.format_time(value, format='long'), u'16:36:05 +0000')
        self.assertEqual(i18n.format_time(value, format='long'), u'16h36min05s +0000')
        #self.assertEqual(i18n.format_time(value, format='full'), u'16h36min05s Horário Mundo (GMT)')
        self.assertEqual(i18n.format_time(value, format='full'), u'16h36min05s GMT+00:00')

        i18n.set_timezone('America/Chicago')
        self.assertEqual(i18n.format_time(value, format='short'), u'10:36')

    def test_parse_date(self):
        i18n.set_locale('en_US')
        self.assertEqual(i18n.parse_date('4/1/04'), datetime.date(2004, 4, 1))
        i18n.set_locale('de_DE')
        self.assertEqual(i18n.parse_date('01.04.2004'), datetime.date(2004, 4, 1))

    def test_parse_datetime(self):
        i18n.set_locale('en_US')
        self.assertRaises(NotImplementedError, i18n.parse_datetime, '4/1/04 16:08:09')

    def test_parse_time(self):
        i18n.set_locale('en_US')
        self.assertEqual(i18n.parse_time('18:08:09'), datetime.time(18, 8, 9))
        i18n.set_locale('de_DE')
        self.assertEqual(i18n.parse_time('18:08:09'), datetime.time(18, 8, 9))

    def test_format_timedelta(self):
        # This is only present in Babel dev, so skip if not available.
        if not getattr(i18n, 'format_timedelta', None):
            return

        i18n.set_locale('en_US')
        # ???
        # self.assertEqual(i18n.format_timedelta(datetime.timedelta(weeks=12)), u'3 months')
        self.assertEqual(i18n.format_timedelta(datetime.timedelta(weeks=12)), u'3 mths')
        i18n.set_locale('es')
        # self.assertEqual(i18n.format_timedelta(datetime.timedelta(seconds=1)), u'1 segundo')
        self.assertEqual(i18n.format_timedelta(datetime.timedelta(seconds=1)), u'1 s')
        i18n.set_locale('en_US')
        self.assertEqual(i18n.format_timedelta(datetime.timedelta(hours=3), granularity='day'), u'1 day')
        self.assertEqual(i18n.format_timedelta(datetime.timedelta(hours=23), threshold=0.9), u'1 day')
        # self.assertEqual(i18n.format_timedelta(datetime.timedelta(hours=23), threshold=1.1), u'23 hours')
        self.assertEqual(i18n.format_timedelta(datetime.timedelta(hours=23), threshold=1.1), u'23 hrs')
        self.assertEqual(i18n.format_timedelta(datetime.datetime.now() - datetime.timedelta(days=5)), u'5 days')

    def test_format_iso(self):
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(i18n.format_date(value, format='iso'), u'2009-11-10')
        self.assertEqual(i18n.format_time(value, format='iso'), u'16:36:05')
        self.assertEqual(i18n.format_datetime(value, format='iso'), u'2009-11-10T16:36:05+0000')

    #==========================================================================
    # Timezones
    #==========================================================================

    def test_set_timezone(self):
        request = get_request()
        request.i18n.set_timezone('UTC')
        self.assertEqual(request.i18n.tzinfo.zone, 'UTC')

        request.i18n.set_timezone('America/Chicago')
        self.assertEqual(request.i18n.tzinfo.zone, 'America/Chicago')

        request.i18n.set_timezone('America/Sao_Paulo')
        self.assertEqual(request.i18n.tzinfo.zone, 'America/Sao_Paulo')

    def test_to_local_timezone(self):
        request = get_request()
        request.i18n.set_timezone('US/Eastern')

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
        request = get_request()
        request.i18n.set_timezone('US/Eastern')

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
        i18n.set_locale('de_DE')
        self.assertEqual(i18n.get_timezone_location(pytz.timezone('America/St_Johns')), u'Kanada (St. John\'s)')
        i18n.set_locale('de_DE')
        self.assertEqual(i18n.get_timezone_location(pytz.timezone('America/Mexico_City')), u'Mexiko (Mexiko-Stadt)')
        i18n.set_locale('de_DE')
        self.assertEqual(i18n.get_timezone_location(pytz.timezone('Europe/Berlin')), u'Deutschland')

    #==========================================================================
    # Number formatting
    #==========================================================================

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

    #==========================================================================
    # Miscelaneous
    #==========================================================================

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


if __name__ == '__main__':
    test_utils.main()
