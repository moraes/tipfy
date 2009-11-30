# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.i18n
"""
import unittest
import gettext as gettext_stdlib
import datetime
from nose.tools import raises

from _base import get_app, get_environ, get_request, get_response
from tipfy import local
from tipfy.ext.i18n import locale, translations, set_locale, gettext, _, \
    ngettext, lazy_gettext, lazy_ngettext, format_datetime, format_time, \
    format_date, get_tzinfo, to_local_timezone, to_utc, pytz, set_app_hooks


class TestI18n(unittest.TestCase):
    def tearDown(self):
        local.app = None
        local.locale = None
        local.translations = None

    #===========================================================================
    # Translations
    #===========================================================================
    def test_set_locale(self):
        assert local.locale is None
        assert local.translations is None

        set_locale('pt_BR')
        assert local.locale == 'pt_BR'
        assert isinstance(local.translations, gettext_stdlib.NullTranslations)

    @raises(AttributeError)
    def test_translations_not_set(self):
        gettext('foo')

    def test_gettext(self):
        set_locale('en_US')
        assert gettext('foo') == u'foo'

    def test_gettext_(self):
        set_locale('en_US')
        assert _('foo') == u'foo'

    def test_ngettext(self):
        set_locale('en_US')
        assert ngettext('One foo', 'Many foos', 1) == u'One foo'
        assert ngettext('One foo', 'Many foos', 2) == u'Many foos'

    def test_lazy_gettext(self):
        set_locale('en_US')
        assert lazy_gettext('foo') == u'foo'

    def test_lazy_ngettext(self):
        set_locale('en_US')
        assert lazy_ngettext('One foo', 'Many foos', 1) == u'One foo'
        assert lazy_ngettext('One foo', 'Many foos', 2) == u'Many foos'

    #===========================================================================
    # Date formatting
    #===========================================================================
    def test_format_date(self):
        app = get_app()
        app.config.update('tipfy.ext.i18n', {'timezone': 'UTC'})

        set_locale('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert format_date(value, format='short') == u'11/10/09'
        assert format_date(value, format='medium') == u'Nov 10, 2009'
        assert format_date(value, format='long') == u'November 10, 2009'
        assert format_date(value, format='full') == u'Tuesday, November 10, 2009'

    def test_format_date_pt_BR(self):
        app = get_app()
        app.config.update('tipfy.ext.i18n', {'timezone': 'UTC'})

        set_locale('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert format_date(value, format='short') == u'10/11/09'
        assert format_date(value, format='medium') == u'10/11/2009'
        assert format_date(value, format='long') == u'10 de novembro de 2009'
        assert format_date(value, format='full') == u'terça-feira, 10 de novembro de 2009'

    def test_format_datetime(self):
        app = get_app()
        app.config.update('tipfy.ext.i18n', {'timezone': 'UTC'})

        set_locale('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert format_datetime(value, format='short') == u'11/10/09 4:36 PM'
        assert format_datetime(value, format='medium') == u'Nov 10, 2009 4:36:05 PM'
        assert format_datetime(value, format='long') == u'November 10, 2009 4:36:05 PM +0000'
        assert format_datetime(value, format='full') == u'Tuesday, November 10, 2009 4:36:05 PM World (GMT) Time'

    def test_format_datetime_pt_BR(self):
        app = get_app()
        app.config.update('tipfy.ext.i18n', {'timezone': 'UTC'})

        set_locale('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert format_datetime(value, format='short') == u'10/11/09 16:36'
        assert format_datetime(value, format='medium') == u'10/11/2009 16:36:05'
        assert format_datetime(value, format='long') == u'10 de novembro de 2009 16:36:05 +0000'
        assert format_datetime(value, format='full') == u'terça-feira, 10 de novembro de 2009 16h36min05s Horário Mundo (GMT)'

    def test_format_time(self):
        app = get_app()
        app.config.update('tipfy.ext.i18n', {'timezone': 'UTC'})

        set_locale('en_US')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert format_time(value, format='short') == u'4:36 PM'
        assert format_time(value, format='medium') == u'4:36:05 PM'
        assert format_time(value, format='long') == u'4:36:05 PM +0000'
        assert format_time(value, format='full') == u'4:36:05 PM World (GMT) Time'

    def test_format_time_pt_BR(self):
        app = get_app()
        app.config.update('tipfy.ext.i18n', {'timezone': 'UTC'})

        set_locale('pt_BR')
        value = datetime.datetime(2009, 11, 10, 16, 36, 05)

        assert format_time(value, format='short') == u'16:36'
        assert format_time(value, format='medium') == u'16:36:05'
        assert format_time(value, format='long') == u'16:36:05 +0000'
        assert format_time(value, format='full') == u'16h36min05s Horário Mundo (GMT)'

    #===========================================================================
    # Timezones
    #===========================================================================
    def test_default_get_tzinfo(self):
        app = get_app()
        app.config.update('tipfy.ext.i18n', {'timezone': 'UTC'})
        assert get_tzinfo().zone == 'UTC'

        app.config.update('tipfy.ext.i18n', {'timezone': 'America/Chicago'})
        assert get_tzinfo().zone == 'America/Chicago'

        app.config.update('tipfy.ext.i18n', {'timezone': 'America/Sao_Paulo'})
        assert get_tzinfo().zone == 'America/Sao_Paulo'

    def test_get_tzinfo(self):
        tzinfo = get_tzinfo('UTC')
        assert tzinfo.zone == 'UTC'

        tzinfo = get_tzinfo('America/Chicago')
        assert tzinfo.zone == 'America/Chicago'

        tzinfo = get_tzinfo('America/Sao_Paulo')
        assert tzinfo.zone == 'America/Sao_Paulo'

    def test_to_local_timezone(self):
        app = get_app()
        app.config.update('tipfy.ext.i18n', {'timezone': 'US/Eastern'})
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
        app = get_app()
        app.config.update('tipfy.ext.i18n', {'timezone': 'US/Eastern'})
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
    # App hooks
    #===========================================================================
    def test_set_app_hooks(self):
        app = get_app()

        assert 'pre_dispatch_handler' not in app.hooks.hooks
        assert 'pre_send_response' not in app.hooks.hooks

        set_app_hooks(app)

        assert 'pre_dispatch_handler' in app.hooks.hooks
        assert 'pre_send_response' in app.hooks.hooks
