# -*- coding: utf-8 -*-
"""
    tipfy.config
    ~~~~~~~~~~~~

    Configuration object.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from werkzeug import import_string

# Value used for required values.
REQUIRED_VALUE = object()

# Value used for missing default values.
DEFAULT_VALUE = object()


class Config(dict):
    """A simple configuration dictionary keyed by module name. This is a
    dictionary of dictionaries. It requires all values to be dictionaries
    and applies updates and default values to the inner dictionaries instead
    of the first level one.

    The configuration object is available as a ``config`` attribute of
    :class:`Tipfy`. If is instantiated and populated when the app is built::

        config = {}

        config['my.module'] = {
            'foo': 'bar',
        }

        app = Tipfy(rules=[Rule('/', name='home', handler=MyHandler)], config=config)

    Then to read configuration values, use :meth:`RequestHandler.get_config`::

        class MyHandler(RequestHandler):
            def get(self):
                foo = self.get_config('my.module', 'foo')

                # ...
    """
    #: Loaded module configurations.
    loaded = None

    def __init__(self, values=None, defaults=None):
        """Initializes the configuration object.

        :param values:
            A dictionary of configuration dictionaries for modules.
        :param defaults:
            A dictionary of configuration dictionaries for initial default
            values. These modules are marked as loaded.
        """
        self.loaded = []
        if values is not None:
            assert isinstance(values, dict)
            for module, config in values.iteritems():
                self.update(module, config)

        if defaults is not None:
            assert isinstance(defaults, dict)
            for module, config in defaults.iteritems():
                self.setdefault(module, config)
                self.loaded.append(module)

    def __getitem__(self, module):
        """Returns a configuration for a module.

        :param module:
            A module name for the configuration, e.g.: `tipfy.ext.i18n`.
        :returns:
            A dictionary of configurations for the module.
        """
        """
        if module in self and module in self.loaded:
            return dict.__getitem__(self, module)

        return self.get(module)
        """
        if module not in self.loaded:
            return self.get(module)

        return dict.__getitem__(self, module)

    def __setitem__(self, module, values):
        """Sets a configuration for a module, requiring it to be a dictionary.

        :param module:
            A module name for the configuration, e.g.: `tipfy.ext.i18n`.
        :param values:
            A dictionary of configurations for the module.
        """
        assert isinstance(values, dict)
        dict.__setitem__(self, module, values)

    def get(self, module, key=None, default=REQUIRED_VALUE):
        """Returns a configuration value for a module. If it is not already
        set, loads a ``default_config`` variable from the given module,
        updates the app configuration with those default values and returns
        the value for the given key. If the key is still not available,
        returns the provided default value or raises an exception if no
        default was provided.

        Every module that allows some kind of configuration sets a
        ``default_config`` global variable that is loaded by this function,
        cached and used in case the requested configuration was not defined
        by the user.

        :param module:
            The configured module.
        :param key:
            The config key.
        :param default:
            A default value to return in case the configuration for
            the module/key is not set.
        :returns:
            A configuration value.
        """
        if module not in self.loaded:
            # Load default configuration and update config.
            values = import_string(module + '.default_config', silent=True)
            if values:
                self.setdefault(module, values)

            self.loaded.append(module)

        try:
            value = dict.__getitem__(self, module)
        except KeyError:
            raise KeyError('Module %r is not configured.' % module)

        if key is None:
            return value

        return value.get(key, default)

    def setdefault(self, module, values):
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
            The module to set default configuration, e.g.: `tipfy.ext.i18n`.
        :param values:
            A dictionary of configurations for the module.
        :returns:
            None.
        """
        assert isinstance(values, dict)
        if module not in self:
            dict.__setitem__(self, module, SubConfig(module))

        for key, value in values.iteritems():
            dict.__getitem__(self, module).setdefault(key, value)

    def update(self, module, values):
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
            The module to update the configuration, e.g.: `tipfy.ext.i18n`.
        :param values:
            A dictionary of configurations for the module.
        :returns:
            None.
        """
        assert isinstance(values, dict)
        if module not in self:
            dict.__setitem__(self, module, SubConfig(module))

        dict.__getitem__(self, module).update(values)


class SubConfig(dict):
    def __init__(self, module, values=None):
        dict.__init__(self, values or ())
        self.module = module

    def __getitem__(self, key):
        try:
            value = dict.__getitem__(self, key)
        except KeyError:
            raise KeyError('Module %r does not have the config key %r' %
                (self.module, key))

        if value is REQUIRED_VALUE:
            raise KeyError('Module %r requires the config key %r to be '
                'set.' % (self.module, key))

        return value

    def get(self, key, default=None):
        if key not in self:
            value = default
        else:
            value = dict.__getitem__(self, key)

        if value is REQUIRED_VALUE:
            raise KeyError('Module %r requires the config key %r to be '
                'set.' % (self.module, key))

        return value
