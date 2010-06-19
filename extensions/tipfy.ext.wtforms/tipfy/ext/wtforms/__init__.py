# -*- coding: utf-8 -*-
"""
    tipfy.ext.wtforms
    ~~~~~~~~~~~~~~~~~

    Enhanced WTForms form library support for tipfy.

    :copyright: 2010 WTForms authors.
    :copyright: 2010 tipfy.org.
    :copyright: 2009 Plurk Inc.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import REQUIRED_VALUE
from tipfy.ext.wtforms import validators, widgets
from tipfy.ext.wtforms.fields import *
from tipfy.ext.wtforms.form import Form
from tipfy.ext.wtforms.validators import ValidationError


#: Default configuration values for this module. Keys are:
#:
#: - ``recaptcha_use_ssl``: ``True`` to use SSL for ReCaptcha requests,
#:   ``False`` otherwise.
#:
#: - ``recaptcha_public_key``: Public key for ReCaptcha.
#:
#: - ``recaptcha_private_key``: Private key for ReCaptcha.
default_config = {
    'recaptcha_use_ssl':     False,
    'recaptcha_public_key':  REQUIRED_VALUE,
    'recaptcha_private_key': REQUIRED_VALUE,
}
