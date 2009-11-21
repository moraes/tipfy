# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.i18n
"""
import unittest
import datetime
from _base import get_app, get_environ, get_request, get_response


class TestI18n(unittest.TestCase):
    def setUp(self):
        from tipfy import local
        local.locale = None
        local.translations = None

        self.app = get_app()
        self.old_timezone = self.app.config.timezone

    def tearDown(self):
        self.app.config.timezone = self.old_timezone

    def test_set_locale(self):
        from tipfy import local
        import gettext
        from tipfy.ext.i18n import set_locale, locale, translations

        self.assertEqual(local.locale, None)
        self.assertEqual(local.translations, None)

        set_locale('pt_BR')
        self.assertEqual(local.locale, 'pt_BR')
        self.assertEqual(isinstance(local.translations, gettext.NullTranslations), True)

    def test_translations_not_set(self):
        from tipfy.ext.i18n import gettext
        self.assertRaises(AttributeError, gettext, 'foo')

    def test_gettext(self):
        from tipfy.ext.i18n import set_locale, gettext

        set_locale('en_US')
        self.assertEqual(gettext('foo'), u'foo')

    def test_gettext_(self):
        from tipfy.ext.i18n import set_locale, _

        set_locale('en_US')
        self.assertEqual(_('foo'), u'foo')

    def test_ngettext(self):
        from tipfy.ext.i18n import set_locale, ngettext

        set_locale('en_US')
        self.assertEqual(ngettext('One foo', 'Many foos', 1), u'One foo')
        self.assertEqual(ngettext('One foo', 'Many foos', 2), u'Many foos')

    def test_lazy_gettext(self):
        from tipfy.ext.i18n import set_locale, lazy_gettext

        set_locale('en_US')
        self.assertEqual(lazy_gettext('foo'), u'foo')

    def test_lazy_ngettext(self):
        from tipfy.ext.i18n import set_locale, lazy_ngettext

        set_locale('en_US')
        self.assertEqual(lazy_ngettext('One foo', 'Many foos', 1), u'One foo')
        self.assertEqual(lazy_ngettext('One foo', 'Many foos', 2), u'Many foos')

    def test_format_date(self):
        from tipfy.ext.i18n import set_locale, format_date

        set_locale('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(format_date(value, format='short'), u'11/10/09')
        self.assertEqual(format_date(value, format='medium'), u'Nov 10, 2009')
        self.assertEqual(format_date(value, format='long'), u'November 10, 2009')
        self.assertEqual(format_date(value, format='full'), u'Tuesday, November 10, 2009')

        set_locale('pt_BR')
        self.assertEqual(format_date(value, format='short'), u'10/11/09')
        self.assertEqual(format_date(value, format='medium'), u'10/11/2009')
        self.assertEqual(format_date(value, format='long'), u'10 de novembro de 2009')
        self.assertEqual(format_date(value, format='full'), u'terça-feira, 10 de novembro de 2009')

    def test_format_datetime(self):
        from tipfy.ext.i18n import set_locale, format_datetime
        self.app.config.timezone = 'UTC'

        set_locale('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(format_datetime(value, format='short'), u'11/10/09 4:36 PM')
        self.assertEqual(format_datetime(value, format='medium'), u'Nov 10, 2009 4:36:05 PM')
        self.assertEqual(format_datetime(value, format='long'), u'November 10, 2009 4:36:05 PM +0000')
        self.assertEqual(format_datetime(value, format='full'), u'Tuesday, November 10, 2009 4:36:05 PM World (GMT) Time')

        set_locale('pt_BR')
        self.assertEqual(format_datetime(value, format='short'), u'10/11/09 16:36')
        self.assertEqual(format_datetime(value, format='medium'), u'10/11/2009 16:36:05')
        self.assertEqual(format_datetime(value, format='long'), u'10 de novembro de 2009 16:36:05 +0000')
        self.assertEqual(format_datetime(value, format='full'), u'terça-feira, 10 de novembro de 2009 16h36min05s Horário Mundo (GMT)')

    def test_format_time(self):
        from tipfy.ext.i18n import set_locale, format_time
        self.app.config.timezone = 'UTC'

        set_locale('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        self.assertEqual(format_time(value, format='short'), u'4:36 PM')
        self.assertEqual(format_time(value, format='medium'), u'4:36:05 PM')
        self.assertEqual(format_time(value, format='long'), u'4:36:05 PM +0000')
        self.assertEqual(format_time(value, format='full'), u'4:36:05 PM World (GMT) Time')

        set_locale('pt_BR')
        self.assertEqual(format_time(value, format='short'), u'16:36')
        self.assertEqual(format_time(value, format='medium'), u'16:36:05')
        self.assertEqual(format_time(value, format='long'), u'16:36:05 +0000')
        self.assertEqual(format_time(value, format='full'), u'16h36min05s Horário Mundo (GMT)')

    def test_default_get_tzinfo(self):
        from tipfy.ext.i18n import get_tzinfo

        self.app.config.timezone = 'UTC'
        self.assertEqual(get_tzinfo().zone, 'UTC')

        self.app.config.timezone = 'America/Chicago'
        self.assertEqual(get_tzinfo().zone, 'America/Chicago')

        self.app.config.timezone = 'America/Sao_Paulo'
        self.assertEqual(get_tzinfo().zone, 'America/Sao_Paulo')

    def test_get_tzinfo(self):
        from tipfy.ext.i18n import get_tzinfo

        tzinfo = get_tzinfo('UTC')
        self.assertEqual(tzinfo.zone, 'UTC')

        tzinfo = get_tzinfo('America/Chicago')
        self.assertEqual(tzinfo.zone, 'America/Chicago')

        tzinfo = get_tzinfo('America/Sao_Paulo')
        self.assertEqual(tzinfo.zone, 'America/Sao_Paulo')

    def test_to_local_timezone(self):
        from tipfy.ext.i18n import to_local_timezone, pytz

        self.app.config.timezone = 'US/Eastern'
        format = '%Y-%m-%d %H:%M:%S %Z%z'

        # Test datetime with timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0, tzinfo=pytz.UTC)
        localtime = to_local_timezone(base)
        formatted = localtime.strftime(format)
        self.assertEqual('2002-10-27 01:00:00 EST-0500', formatted)

        # Test naive datetime - no timezone set
        base = datetime.datetime(2002, 10, 27, 6, 0, 0)
        localtime = to_local_timezone(base)
        formatted = localtime.strftime(format)
        self.assertEqual('2002-10-27 01:00:00 EST-0500', formatted)
