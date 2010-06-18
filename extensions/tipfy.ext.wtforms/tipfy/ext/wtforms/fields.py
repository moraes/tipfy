# -*- coding: utf-8 -*-
"""
    tipfy.ext.wtforms.fields
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Form fields.

    :copyright: 2010 tipfy.org.
    :copyright: 2010 WTForms authors.
    :license: BSD, see LICENSE.txt for more details.
"""
from wtforms.fields import (BooleanField, DecimalField, DateField,
    DateTimeField, FieldList, FloatField, FormField, HiddenField, IntegerField,
    PasswordField, RadioField, SelectField, SelectMultipleField, SubmitField,
    TextField, TextAreaField)
from wtforms import widgets


class FileField(TextField):
    widget = widgets.FileInput()

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[0]
        else:
            self.data = u''

    def _value(self):
        return u''
