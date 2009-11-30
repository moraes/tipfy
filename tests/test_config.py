# -*- coding: utf-8 -*-
"""
    Tests for tipfy.Config and tipfy.get_config.
"""
import unittest
from nose.tools import assert_raises

from _base import get_app
from tipfy import Config, get_config, default_config


class TestConfig(unittest.TestCase):
    def test_get(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        assert config.get('bar') is None
        assert config.get('foo') == {
            'bar': 'baz',
            'doo': 'ding',
        }

        assert config.get('foo', 'bar') == 'baz'
        assert config.get('foo', 'doo') == 'ding'
        assert config.get('foo', 'hmm') is None
        assert config.get('foo', 'hmm', 'default') == 'default'

    def test_update(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        assert config['foo']['bar'] == 'baz'
        assert config['foo']['doo'] == 'ding'

        config.update('foo', {'bar': 'other'})

        assert config['foo']['bar'] == 'other'
        assert config['foo']['doo'] == 'ding'

    def test_setdefault(self):
        config = Config()

        assert config.get('foo') is None

        config.setdefault('foo', {
            'bar': 'baz',
            'doo': 'ding',
        })

        assert config['foo']['bar'] == 'baz'
        assert config['foo']['doo'] == 'ding'

    def test_setitem(self):
        config = Config()

        def setitem(key, value):
            config[key] = value
            return config

        assert setitem('foo', {'bar': 'baz'}) == {'foo': {'bar': 'baz'}}

    def test_init_no_dict_values(self):
        assert_raises(AssertionError, Config, {'foo': 'bar'})
        assert_raises(AssertionError, Config, {'foo': None})
        assert_raises(AssertionError, Config, 'foo')

    def test_update_no_dict_values(self):
        config = Config()

        assert_raises(AssertionError, config.update, {'foo': 'bar'}, 'baz')
        assert_raises(AssertionError, config.update, {'foo': None}, 'baz')
        assert_raises(AssertionError, config.update, 'foo', 'bar')

    def test_setdefault_no_dict_values(self):
        config = Config()

        assert_raises(AssertionError, config.setdefault, 'foo', 'bar')
        assert_raises(AssertionError, config.setdefault, 'foo', None)

    def test_setitem_no_dict_values(self):
        config = Config()

        def setitem(key, value):
            config[key] = value
            return config

        assert_raises(AssertionError, setitem, 'foo', 'bar')
        assert_raises(AssertionError, setitem, 'foo', None)

class TestGetConfig(unittest.TestCase):
    def test_default_config(self):
        app = get_app()

        assert get_config('tipfy', 'dev') == default_config['dev']
        assert get_config('tipfy.ext.jinja2', 'templates_dir') == 'templates'
        assert get_config('tipfy.ext.i18n', 'locale') == 'en_US'
        assert get_config('tipfy.ext.i18n', 'timezone') == 'America/Chicago'

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

        assert get_config('tipfy', 'dev') is True
        assert get_config('tipfy.ext.jinja2', 'templates_dir') == 'apps/templates'
        assert get_config('tipfy.ext.i18n', 'locale') == 'pt_BR'
        assert get_config('tipfy.ext.i18n', 'timezone') == 'America/Sao_Paulo'

    def test_override_config2(self):
        app = get_app({
            'tipfy.ext.i18n': {
                'timezone': 'America/Sao_Paulo',
            },
        })

        assert get_config('tipfy.ext.i18n', 'locale') == 'en_US'
        assert get_config('tipfy.ext.i18n', 'timezone') == 'America/Sao_Paulo'
