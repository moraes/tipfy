# -*- coding: utf-8 -*-
"""
    Tests for tipfy.config
"""
import unittest

from nose.tools import assert_raises, raises

import _base

import tipfy


class TestConfig(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_get_existing_keys(self):
        config = tipfy.Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        assert config.get('foo', 'bar') == 'baz'
        assert config.get('foo', 'doo') == 'ding'

    def test_get_non_existing_keys(self):
        config = tipfy.Config()

        assert config.get('foo', 'bar') is None

    def test_get_dict_existing_keys(self):
        config = tipfy.Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        assert config.get('foo') == {
            'bar': 'baz',
            'doo': 'ding',
        }

    def test_get_dict_non_existing_keys(self):
        config = tipfy.Config()

        assert config.get('bar') is None

    def test_get_with_default(self):
        config = tipfy.Config()

        assert config.get('foo', 'bar', 'ooops') == 'ooops'
        assert config.get('foo', 'doo', 'wooo') == 'wooo'

    def test_get_with_default_and_none(self):
        config = tipfy.Config({'foo': {
            'bar': None,
        }})

        assert config.get('foo', 'bar', 'ooops') == None

    def test_update(self):
        config = tipfy.Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        assert config.get('foo', 'bar') == 'baz'
        assert config.get('foo', 'doo') == 'ding'

        config.update('foo', {'bar': 'other'})

        assert config.get('foo', 'bar') == 'other'
        assert config.get('foo', 'doo') == 'ding'

    def test_setdefault(self):
        config = tipfy.Config()

        assert config.get('foo') is None

        config.setdefault('foo', {
            'bar': 'baz',
            'doo': 'ding',
        })

        assert config.get('foo', 'bar') == 'baz'
        assert config.get('foo', 'doo') == 'ding'

    def test_setdefault2(self):
        config = tipfy.Config({'foo': {
            'bar': 'baz',
        }})

        assert config.get('foo') == {
            'bar': 'baz',
        }

        config.setdefault('foo', {
            'bar': 'wooo',
            'doo': 'ding',
        })

        assert config.get('foo', 'bar') == 'baz'
        assert config.get('foo', 'doo') == 'ding'

    def test_setitem(self):
        config = tipfy.Config()

        def setitem(key, value):
            config[key] = value
            return config

        assert setitem('foo', {'bar': 'baz'}) == {'foo': {'bar': 'baz'}}

    def test_init_no_dict_values(self):
        assert_raises(AssertionError, tipfy.Config, {'foo': 'bar'})
        assert_raises(AssertionError, tipfy.Config, {'foo': None})
        assert_raises(AssertionError, tipfy.Config, 'foo')

    def test_update_no_dict_values(self):
        config = tipfy.Config()

        assert_raises(AssertionError, config.update, {'foo': 'bar'}, 'baz')
        assert_raises(AssertionError, config.update, {'foo': None}, 'baz')
        assert_raises(AssertionError, config.update, 'foo', 'bar')

    def test_setdefault_no_dict_values(self):
        config = tipfy.Config()

        assert_raises(AssertionError, config.setdefault, 'foo', 'bar')
        assert_raises(AssertionError, config.setdefault, 'foo', None)

    def test_setitem_no_dict_values(self):
        config = tipfy.Config()

        def setitem(key, value):
            config[key] = value
            return config

        assert_raises(AssertionError, setitem, 'foo', 'bar')
        assert_raises(AssertionError, setitem, 'foo', None)


class TestGetConfig(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_default_config(self):
        app = tipfy.WSGIApplication()

        from tipfy.ext.jinja2 import default_config as jinja2_config
        from tipfy.ext.i18n import default_config as i18n_config

        assert tipfy.get_config('tipfy', 'dev') == tipfy.default_config['dev']
        assert tipfy.get_config('tipfy.ext.jinja2', 'templates_dir') == jinja2_config['templates_dir']
        assert tipfy.get_config('tipfy.ext.i18n', 'locale') == i18n_config['locale']
        assert tipfy.get_config('tipfy.ext.i18n', 'timezone') == i18n_config['timezone']

    def test_default_config_with_non_existing_key(self):
        app = tipfy.WSGIApplication()

        from tipfy.ext.i18n import default_config as i18n_config

        # In the first time the module config will be loaded normally.
        assert tipfy.get_config('tipfy.ext.i18n', 'locale') == i18n_config['locale']

        # In the second time it won't be loaded, but won't find the value and then use the default.
        assert tipfy.get_config('tipfy.ext.i18n', 'i_dont_exist', 'foo') == 'foo'

    def test_override_config(self):
        app = tipfy.WSGIApplication({
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

        assert tipfy.get_config('tipfy', 'dev') is True
        assert tipfy.get_config('tipfy.ext.jinja2', 'templates_dir') == 'apps/templates'
        assert tipfy.get_config('tipfy.ext.i18n', 'locale') == 'pt_BR'
        assert tipfy.get_config('tipfy.ext.i18n', 'timezone') == 'America/Sao_Paulo'

    def test_override_config2(self):
        app = tipfy.WSGIApplication({
            'tipfy.ext.i18n': {
                'timezone': 'America/Sao_Paulo',
            },
        })

        assert tipfy.get_config('tipfy.ext.i18n', 'locale') == 'en_US'
        assert tipfy.get_config('tipfy.ext.i18n', 'timezone') == 'America/Sao_Paulo'

    def test_get(self):
        app = tipfy.WSGIApplication({'foo': {
            'bar': 'baz',
        }})

        assert tipfy.get_config('foo', 'bar') == 'baz'

    def test_get_with_default(self):
        app = tipfy.WSGIApplication()

        assert tipfy.get_config('tipfy.ext.i18n', 'bar', 'baz') == 'baz'

    def test_get_with_default_and_none(self):
        app = tipfy.WSGIApplication({'foo': {
            'bar': None,
        }})

        assert tipfy.get_config('foo', 'bar', 'ooops') == None

    def test_get_with_default_and_module_load(self):
        app = tipfy.WSGIApplication()
        assert tipfy.get_config('tipfy.ext.i18n', 'locale') == 'en_US'

        app = tipfy.WSGIApplication()
        assert tipfy.get_config('tipfy.ext.i18n', 'locale', 'foo') == 'en_US'

    @raises(KeyError)
    def test_required_config(self):
        app = tipfy.WSGIApplication()
        assert tipfy.get_config('tipfy.ext.i18n', 'i_dont_exist') == 'baz'

    @raises(KeyError)
    def test_required_config2(self):
        app = tipfy.WSGIApplication()
        assert tipfy.get_config('tipfy.ext.session', 'secret_key') == 'baz'

    @raises(AttributeError)
    def test_missing_default_config(self):
        app = tipfy.WSGIApplication()
        assert tipfy.get_config('tipfy.ext.db', 'foo') == 'baz'

    @raises(ImportError)
    def test_missing_module(self):
        app = tipfy.WSGIApplication()
        assert tipfy.get_config('i_dont_exist', 'i_dont_exist') == 'baz'
