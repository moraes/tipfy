# -*- coding: utf-8 -*-
"""
    tipfy.ext.wtforms.fields
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Form fields.

    :copyright: 2010 WTForms authors.
    :copyright: 2010 tipfy.org.
    :copyright: 2009 Plurk Inc.
    :license: BSD, see LICENSE.txt for more details.
"""
from wtforms.fields import (BooleanField, DecimalField, DateField,
    DateTimeField, Field, FieldList, FloatField, FormField, HiddenField,
    IntegerField, PasswordField, RadioField, SelectField, SelectMultipleField,
    SubmitField, TextField, TextAreaField)

from tipfy.ext.wtforms import widgets
from tipfy.ext.wtforms import validators


class CsrfTokenField(HiddenField):
    def __init__(self, *args, **kwargs):
        super(CsrfTokenField, self).__init__(*args, **kwargs)
        self.csrf_token = None
        self.type = 'HiddenField'

    def process_formdata(self, valuelist):
        """
        Process data received over the wire from a form.

        This will be called during form construction with data supplied
        through the `formdata` argument.

        :param valuelist: A list of strings to process.
        """
        if valuelist:
            self.csrf_token = valuelist[0]


class FileField(TextField):
    widget = widgets.FileInput()

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[0]
        else:
            self.data = u''

    def _value(self):
        return u''


class RecaptchaField(Field):
    widget = widgets.RecaptchaWidget()

    #: Set if validation fails.
    recaptcha_error = None

    def __init__(self, *args, **kwargs):
        kwargs['validators'] = [validators.Recaptcha()]
        super(RecaptchaField, self).__init__(*args, **kwargs)
