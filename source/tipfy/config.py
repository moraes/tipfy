# -*- coding: utf-8 -*-
"""
    tipfy.config
    ~~~~~~~~~~~~

    Configuration system.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import import_string, local

# Value to be used for required configuration values.
REQUIRED_CONFIG = object()
# Value used internally for missing default configuration values.
_DEFAULT_CONFIG = object()


class Config(dict):
    """A simple configuration dictionary keyed by module name. This is a
    dictionary of dictionaries. It requires all values to be dictionaries
    and applies updates and default values to the inner dictionaries instead of
    the first level one.
    """
    #: Loaded module configurations.
    modules = None

    def __init__(self, value=None):
        self.modules = []
        if value is not None:
            assert isinstance(value, dict)
            for module in value.keys():
                self.update(module, value[module])

    def __setitem__(self, key, value):
        """Sets a configuration for a module, requiring it to be a dictionary.
        """
        assert isinstance(value, dict)
        super(Config, self).__setitem__(key, value)

    def update(self, module, value):
        """Updates the configuration dictionary for a module.

        >>> cfg = Config({'tipfy.ext.i18n': {'locale': 'pt_BR'})
        >>> cfg.get('tipfy.ext.i18n', 'locale')
        pt_BR
        >>> cfg.get('tipfy.ext.i18n', 'foo')
        None
        >>> cfg.update('tipfy.ext.i18n', {'locale': 'en_US', 'foo': 'bar'})
        >>> cfg.get('tipfy.ext.i18n', 'locale')
        en_US
        >>> cfg.get('tipfy.ext.i18n', 'foo')
        bar

        :param module:
            The module to update the configuration, e.g.: 'tipfy.ext.i18n'.
        :param value:
            A dictionary of configurations for the module.
        :return:
            None.
        """
        assert isinstance(value, dict)
        if module not in self:
            self[module] = {}

        self[module].update(value)

    def setdefault(self, module, value):
        """Sets a default configuration dictionary for a module.

        >>> cfg = Config({'tipfy.ext.i18n': {'locale': 'pt_BR'})
        >>> cfg.get('tipfy.ext.i18n', 'locale')
        pt_BR
        >>> cfg.get('tipfy.ext.i18n', 'foo')
        None
        >>> cfg.setdefault('tipfy.ext.i18n', {'locale': 'en_US', 'foo': 'bar'})
        >>> cfg.get('tipfy.ext.i18n', 'locale')
        pt_BR
        >>> cfg.get('tipfy.ext.i18n', 'foo')
        bar

        :param module:
            The module to set default configuration, e.g.: 'tipfy.ext.i18n'.
        :param value:
            A dictionary of configurations for the module.
        :return:
            None.
        """
        assert isinstance(value, dict)
        if module not in self:
            self[module] = {}

        for key in value.keys():
            self[module].setdefault(key, value[key])

    def get(self, module, key=None, default=None):
        """Returns a configuration value for given key in a given module.

        >>> cfg = Config({'tipfy.ext.i18n': {'locale': 'pt_BR'})
        >>> cfg.get('tipfy.ext.i18n')
        {'locale': 'pt_BR'}
        >>> cfg.get('tipfy.ext.i18n', 'locale')
        pt_BR
        >>> cfg.get('tipfy.ext.i18n', 'invalid-key')
        None
        >>> cfg.get('tipfy.ext.i18n', 'invalid-key', 'default-value')
        default-value

        :param module:
            The module to get a configuration from, e.g.: 'tipfy.ext.i18n'.
        :param key:
            The key from the module configuration.
        :param default:
            A default value to return in case the configuration for the
            module/key is not set.
        :return:
            The configuration value.
        """
        if module not in self:
            return default

        if key is None:
            return self[module]
        elif key not in self[module]:
            return default

        return self[module][key]


def get_config(module, key=None, default=_DEFAULT_CONFIG):
    """Returns a configuration value for a module. If it is not already set,
    loads a ``default_config`` variable from the given module, update the app
    config with those default values and return the value for the given key.
    If the key is still not available, returns the provided default value or
    raises an exception if no default was provided.

    Every `Tipfy`_ module that allows some kind of configuration sets a
    ``default_config`` global variable that is loaded by this function, cached
    and used in case the requested configuration was not defined by the user.

    :param module:
        The configured module.
    :param key:
        The config key.
    :return:
        A configuration value.
    """
    value = local.app.config.get(module, key, _DEFAULT_CONFIG)
    if value not in (_DEFAULT_CONFIG, REQUIRED_CONFIG):
        return value

    if default is _DEFAULT_CONFIG:
        # If no default was provided, the config is required.
        default = REQUIRED_CONFIG

    if value is _DEFAULT_CONFIG:
        if module not in local.app.config.modules:
            # Update app config. If import fails or the default_config attribute
            # doesn't exist, an exception will be raised.
            local.app.config.setdefault(module, import_string(
                module + ':default_config'))
            local.app.config.modules.append(module)

            value = local.app.config.get(module, key, default)
        else:
            value = default

    if value is REQUIRED_CONFIG:
        raise KeyError('Module %s requires the config key "%s" to be set.' %
            (module, key))

    return value


__all__ = ['Config',
           'get_config',
           'REQUIRED_CONFIG']
