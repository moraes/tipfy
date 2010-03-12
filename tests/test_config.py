# -*- coding: utf-8 -*-
"""
    Tests for tipfy.Config and tipfy.get_config.
"""
import unittest
from nose.tools import assert_raises, raises

from _base import get_app, teardown
from tipfy import Config, default_config, get_config, REQUIRED_CONFIG


class TestConfig(unittest.TestCase):
    def tearDown(self):
        teardown()

    def test_get_existing_keys(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        assert config.get('foo') == {
            'bar': 'baz',
            'doo': 'ding',
        }

        assert config.get('foo', 'bar') == 'baz'
        assert config.get('foo', 'doo') == 'ding'

    def test_get_non_existing_keys(self):
        config = Config()

        assert config.get('bar') is None
        assert config.get('foo', 'bar') is None

    def test_get_with_default(self):
        config = Config()

        assert config.get('foo', 'bar', 'ooops') == 'ooops'
        assert config.get('foo', 'doo', 'wooo') == 'wooo'

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
    def tearDown(self):
        teardown()

    def test_default_config(self):
        app = get_app({})

        from tipfy.ext.jinja2 import default_config as jinja2_config
        from tipfy.ext.i18n import default_config as i18n_config

        assert get_config('tipfy', 'dev') == default_config['dev']
        assert get_config('tipfy.ext.jinja2', 'templates_dir') == jinja2_config['templates_dir']
        assert get_config('tipfy.ext.i18n', 'locale') == i18n_config['locale']
        assert get_config('tipfy.ext.i18n', 'timezone') == i18n_config['timezone']

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

    @raises(ValueError)
    def test_missing_config(self):
        app = get_app({})
        assert get_config('tipfy.ext.i18n', 'i_dont_exist') == 'en_US'

    @raises(AttributeError)
    def test_missing_default_config(self):
        app = get_app({})
        assert get_config('tipfy.ext.db', 'foo') == 'en_US'

    @raises(ImportError)
    def test_missing_module(self):
        app = get_app({})
        assert get_config('i_dont_exist', 'i_dont_exist') == 'en_US'
