# -*- coding: utf-8 -*-
"""
    Tests for tipfy.application

    These tests, for some reason, were causing trouble in test_application.py
    then were moved here.
"""
import unittest

import _base

import tipfy
from tipfy.application import set_extensions_compatibility


class TestMiscelaneous2(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_set_extensions_compatibility(self):
        extensions = [
            'tipfy.ext.debugger',
            'tipfy.ext.appstats',
            'tipfy.ext.i18n',
            'tipfy.ext.session',
            'tipfy.ext.user',
        ]
        middleware = []
        set_extensions_compatibility(extensions, middleware)

        assert extensions == []
        assert middleware == [
            'tipfy.ext.debugger.DebuggerMiddleware',
            'tipfy.ext.appstats.AppstatsMiddleware',
            'tipfy.ext.session.SessionMiddleware',
            'tipfy.ext.auth.AuthMiddleware',
            'tipfy.ext.i18n.I18nMiddleware',
        ]

        extensions = [
            'tipfy.ext.debugger',
            'tipfy.ext.appstats',
            'tipfy.ext.i18n',
            'tipfy.ext.user',
        ]
        middleware = []
        set_extensions_compatibility(extensions, middleware)

        assert extensions == []
        assert middleware == [
            'tipfy.ext.debugger.DebuggerMiddleware',
            'tipfy.ext.appstats.AppstatsMiddleware',
            'tipfy.ext.session.SessionMiddleware',
            'tipfy.ext.auth.AuthMiddleware',
            'tipfy.ext.i18n.I18nMiddleware',
        ]

    def test_set_extensions_compatibility2(self):
        app = tipfy.WSGIApplication({
            'tipfy': {
                'extensions': [
                    'tipfy.ext.debugger',
                    'tipfy.ext.appstats',
                    'tipfy.ext.i18n',
                    'tipfy.ext.session',
                    'tipfy.ext.user',
                ],
            },
        })

        assert app.config.get('tipfy', 'middleware') == [
            'tipfy.ext.debugger.DebuggerMiddleware',
            'tipfy.ext.appstats.AppstatsMiddleware',
            'tipfy.ext.session.SessionMiddleware',
            'tipfy.ext.auth.AuthMiddleware',
            'tipfy.ext.i18n.I18nMiddleware',
        ]

    def test_set_extensions_compatibility3(self):
        app = tipfy.WSGIApplication({
            'tipfy': {
                'extensions': [
                    'tipfy.ext.debugger',
                    'tipfy.ext.appstats',
                    'tipfy.ext.i18n',
                    'tipfy.ext.session',
                    'tipfy.ext.user',
                    'tipfy.ext.i_dont_exist',
                ],
            },
        })

        assert app.config.get('tipfy', 'middleware') == [
            'tipfy.ext.debugger.DebuggerMiddleware',
            'tipfy.ext.appstats.AppstatsMiddleware',
            'tipfy.ext.session.SessionMiddleware',
            'tipfy.ext.auth.AuthMiddleware',
            'tipfy.ext.i18n.I18nMiddleware',
        ]
