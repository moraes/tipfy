# -*- coding: utf-8 -*-
"""
    tipfy.hooks
    ~~~~~~~~~~~

    Hook system.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import werkzeug


class LazyCallable(object):
    """A lazy callable used by :class:`HookHandler`: hooks are set as a string
    and only imported when used.
    """
    def __init__(self, hook_spec):
        """Builds the lazy callable.

        :param hook_spec:
            The callable that will handle the event, as a string. It will be
            imported only when the callable is used.
        """
        self.hook_spec = hook_spec
        self.hook = None

    def __call__(self, *args, **kwargs):
        """Executes the event callable, importing it if it is not imported yet.

        :param args:
            Positional arguments to be passed to the callable.
        :param kwargs:
            Keyword arguments to be passed to the callable.
        :return:
            The value returned by the callable.
        """
        if self.hook is None:
            self.hook = werkzeug.import_string(self.hook_spec)

        return self.hook(*args, **kwargs)


class HookHandler(object):
    def __init__(self, hooks=None):
        """Initializes the application hook handler.

        :param hooks:
            A dictionary with event names as keys and a list of hook specs
            as values.
        """
        self.hooks = hooks or {}

    def add(self, name, hook, pos=None):
        """Adds a hook to a given application event.

        :param name:
            The event name to be added (a string).
        :param hook:
            The callable that is executed when the event occurs. Can be either
            a callable or a string to be lazily imported.
        :param pos:
            Position to insert the hook in the hook list. If not set, the hook
            is appended to the list.
        :return:
            ``None``.
        """
        if not callable(hook):
            hook = LazyCallable(hook)

        event = self.hooks.setdefault(name, [])
        if pos is None:
            event.append(hook)
        else:
            event.insert(pos, hook)

    def add_multi(self, spec):
        """Adds multiple hook to multiple application events.

        :param spec:
            A dictionary with event names as keys and a list of hooks as values.
            Hooks can be a callable or a string to be lazily imported.
        :return:
            ``None``.
        """
        for name in spec.keys():
            for hook in spec[name]:
                self.add(name, hook)

    def iter(self, name, *args, **kwargs):
        """Call all hooks for a given application event. This is a generator.

        :param name:
            The event name (a string).
        :param args:
            Positional arguments to be passed to the subscribers.
        :param kwargs:
            Keyword arguments to be passed to the subscribers.
        :yield:
            The result of the hook calls.
        """
        for hook in self.hooks.get(name, []):
            yield hook(*args, **kwargs)

    def call(self, name, *args, **kwargs):
        """Call all hooks for a given application event. This uses :meth:`iter`
        and returns a list with all results.

        :param name:
            The event name (a string).
        :param args:
            Positional arguments to be passed to the hooks.
        :param kwargs:
            Keyword arguments to be passed to the hooks.
        :return:
            A list with all results from the hook calls.
        """
        return [res for res in self.iter(name, *args, **kwargs)]

    def get(self, name, default=None):
        """Returns the list of hooks added to a given event.

        :param name:
            The event name to get related hooks.
        :param default:
            The default value to return in case the event doesn't have hooks.
        :return:
            A list of hooks.
        """
        return self.hooks.get(name, default)


__all__ = ['HookHandler', 'LazyCallable']
