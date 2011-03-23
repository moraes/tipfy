import ConfigParser
import re


class Converter(object):
    _boolean_states = {
        '1':     True,
        'yes':   True,
        'true':  True,
        'on':    True,
        '0':     False,
        'no':    False,
        'false': False,
        'off':   False,
    }

    def to_boolean(self, value):
        key = value.lower()
        if key not in self._boolean_states:
            raise ValueError('Not a boolean: %r. Booleans must be '
                'one of %s.' % (value, ', '.join(self._boolean_states.keys())))

        return self._boolean_states[key]

    def to_float(self, value):
        return float(value)

    def to_int(self, value):
        return int(value)

    def to_list(self, value):
        value = [line.strip() for line in value.splitlines()]
        return [v for v in value if v]

    def to_unicode(self, value):
        return unicode(value)


class Config(ConfigParser.RawConfigParser):
    """Wraps RawConfigParser `get*()` functions to allow a default to be
    returned instead of throwing errors. Also adds `getlist()` to split
    multi-line values into a list.

    It also implements the magical interpolation behavior similar to the one
    from `SafeConfigParser`, but also supports references to sections.
    This means that values can contain format strings which refer to other
    values in the config file. These variables are replaced on the fly.
    The most basic example is::

        [my_section]
        app_name = my_app
        path = path/to/%(app_name)s

    Here, calling `get('my_section', 'path')` will automatically replace
    variables, resulting in `path/to/my_app`. To get the raw value without
    substitutions, use `get('my_section', 'path', raw=True)`.

    To reference a different section, separate the section and option
    names using a pipe::

        [my_section]
        app_name = my_app

        [my_other_section]
        path = path/to/%(my_section|app_name)s

    If any variables aren't found, a `ConfigParser.InterpolationError`is
    raised.

    Variables are case sensitive, differently from the interpolation behavior
    in `SafeConfigParser`.
    """
    converter = Converter()

    _interpolate_re = re.compile(r"%\(([^)]*)\)s")

    def get(self, section, option, default=None, raw=False):
        converter = self.converter.to_unicode
        return self._get_wrapper(section, option, converter, default, raw)

    def getboolean(self, section, option, default=None, raw=False):
        converter = self.converter.to_boolean
        return self._get_wrapper(section, option, converter, default, raw)

    def getfloat(self, section, option, default=None, raw=False):
        converter = self.converter.to_float
        return self._get_wrapper(section, option, converter, default, raw)

    def getint(self, section, option, default=None, raw=False):
        converter = self.converter.to_int
        return self._get_wrapper(section, option, converter, default, raw)

    def getlist(self, section, option, default=None, raw=False):
        converter = self.converter.to_list
        return self._get_wrapper(section, option, converter, default, raw)

    def _get(self, section, option):
        return ConfigParser.RawConfigParser.get(self, section, option)

    def _get_wrapper(self, sections, option, converter, default, raw):
        """Wraps get functions allowing default values and a list of sections
        looked up in order until a value is found.
        """
        if isinstance(sections, basestring):
            sections = [sections]

        for section in sections:
            try:
                value = self._get(section, option)
                if not raw:
                    value = self._interpolate(section, option, value)

                return converter(value)
            except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                pass
            except ValueError:
                # Failed conversion?
                pass

        return default

    def _interpolate(self, section, option, value, tried=None):
        """Replaces variables avoiding infinite recursion."""
        if not '%(' in value:
            return value

        matches = set(self._interpolate_re.findall(value))
        if not matches:
            return value

        if tried is None:
            tried = [(section, option)]

        variables = {}
        for match in matches:
            parts = tuple(match.split('|', 1))
            if len(parts) == 1:
                new_section, new_option = section, match
            else:
                new_section, new_option = parts

            if parts in tried:
                continue

            tried.append(parts)
            try:
                found = self._get(new_section, new_option)
                tried.append(('DEFAULT', new_option))
                variables[match] = self._interpolate(new_section, new_option,
                    found, tried)
            except Exception:
                pass

        if len(matches) == len(variables):
            return value % variables

        raise ConfigParser.InterpolationError(section, option,
            'Cound not replace %r.' % value)
