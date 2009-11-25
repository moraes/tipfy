# -*- coding: utf-8 -*-
"""
    Tests for tipfy.Config and tipfy.get_config.
"""
import unittest
import sys
from _base import get_app


from tipfy import Config, get_config, default_config


class TestConfig(unittest.TestCase):
    def test_get(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        self.assertEqual(config.get('bar'), None)
        self.assertEqual(config.get('foo'), {
            'bar': 'baz',
            'doo': 'ding',
        })

        self.assertEqual(config.get('foo', 'bar'), 'baz')
        self.assertEqual(config.get('foo', 'doo'), 'ding')
        self.assertEqual(config.get('foo', 'hmm'), None)
        self.assertEqual(config.get('foo', 'hmm', 'default'), 'default')

    def test_update(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        self.assertEqual(config['foo']['bar'], 'baz')
        self.assertEqual(config['foo']['doo'], 'ding')

        config.update({'foo': {'bar': 'other',}})

        self.assertEqual(config['foo']['bar'], 'other')
        self.assertEqual(config['foo']['doo'], 'ding')

    def test_setdefault(self):
        config = Config()

        self.assertEqual(config.get('foo'), None)

        config.setdefault('foo', {
            'bar': 'baz',
            'doo': 'ding',
        })

        self.assertEqual(config['foo']['bar'], 'baz')
        self.assertEqual(config['foo']['doo'], 'ding')


class TestGetConfig(unittest.TestCase):
    def test_default_config(self):
        app = get_app()

        self.assertEqual(get_config('tipfy', 'dev'), default_config['dev'])
        self.assertEqual(get_config('tipfy.ext.jinja2', 'templates_dir'), 'templates')
        self.assertEqual(get_config('tipfy.ext.i18n', 'locale'), 'en_US')
        self.assertEqual(get_config('tipfy.ext.i18n', 'timezone'), 'America/Chicago')

    def test_override_config(self):
        app = get_app({
            'tipfy': {
                'dev': True,
            },
            'tipfy.ext.jinja2': {
                'templates_dir': 'apps/templates'
            },
            'tipfy.ext.i18n': {
                'locale': 'pt_BR',
                'timezone': 'America/Sao_Paulo',
            },
        })

        self.assertEqual(get_config('tipfy', 'dev'), True)
        self.assertEqual(get_config('tipfy.ext.jinja2', 'templates_dir'), 'apps/templates')
        self.assertEqual(get_config('tipfy.ext.i18n', 'locale'), 'pt_BR')
        self.assertEqual(get_config('tipfy.ext.i18n', 'timezone'), 'America/Sao_Paulo')

    def test_override_config2(self):
        app = get_app({
            'tipfy.ext.i18n': {
                'timezone': 'America/Sao_Paulo',
            },
        })

        self.assertEqual(get_config('tipfy.ext.i18n', 'locale'), 'en_US')
        self.assertEqual(get_config('tipfy.ext.i18n', 'timezone'), 'America/Sao_Paulo')
