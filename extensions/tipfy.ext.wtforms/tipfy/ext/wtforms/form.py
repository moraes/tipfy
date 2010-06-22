# -*- coding: utf-8 -*-
"""
    tipfy.ext.wtforms.form
    ~~~~~~~~~~~~~~~~~~~~~~

    Form object.

    :copyright: 2010 tipfy.org.
    :copyright: 2010 WTForms authors.
    :license: BSD, see LICENSE.txt for more details.
"""
from wtforms import Form as BaseForm

from tipfy import Request
from tipfy.ext.wtforms.fields import FileField

try:
    from tipfy.ext import i18n
except ImportError, e:
    i18n = None


class Form(BaseForm):
    def process(self, formdata=None, obj=None, **kwargs):
        """
        Take form, object data, and keyword arg input and have the fields
        process them.

        :param formdata:
            A :class:`tipfy.Request` object or a multidict of form data coming
            from the enduser, usually `request.form` or equivalent.
        :param obj:
            If `formdata` has no data for a field, the form will try to get it
            from the passed object.
        :param `**kwargs`:
            If neither `formdata` or `obj` contains a value for a field, the
            form will assign the value of a matching keyword argument to the
            field, if provided.
        """
        if isinstance(formdata, Request):
            request = formdata
            formdata = request.form
            filedata = request.files
        else:
            filedata = None
            if formdata is not None and not hasattr(formdata, 'getlist'):
                raise TypeError("formdata should be a multidict-type wrapper "
                    "that supports the 'getlist' method")

        for name, field, in self._fields.iteritems():
            if isinstance(field, FileField):
                data = filedata
            else:
                data = formdata

            if obj is not None and hasattr(obj, name):
                field.process(data, getattr(obj, name))
            elif name in kwargs:
                field.process(data, kwargs[name])
            else:
                field.process(data)

    def _get_translations(self):
        ctx = _request_ctx_stack.top

        if ctx is not None and hasattr(ctx, 'babel_instance'):
            return babel.get_translations()

        return None
