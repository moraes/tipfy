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
#: - ``recaptcha_options``: A dictionary of options to customize the look of
#:   the reCAPTCHA widget. See a description of the available options in
#:   the `API docs <http://recaptcha.net/apidocs/captcha/client.html>`_.
#:
#: - ``recaptcha_use_ssl``: ``True`` to use SSL for ReCaptcha requests,
#:   ``False`` otherwise.
#:
#: - ``recaptcha_public_key``: Public key for ReCaptcha.
#:
#: - ``recaptcha_private_key``: Private key for ReCaptcha.
#:
#: - ``csrf_tokens``: Maximum number of CSRF protection tokens to store in
#:   session.
default_config = {
    'recaptcha_options':     None,
    'recaptcha_use_ssl':     False,
    'recaptcha_public_key':  REQUIRED_VALUE,
    'recaptcha_private_key': REQUIRED_VALUE,
    'csrf_tokens':           5,
}
