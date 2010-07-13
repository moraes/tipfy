# -*- coding: utf-8 -*-
"""
    tipfy.ext.wtforms.validators
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Form validators.

    :copyright: 2010 WTForms authors.
    :copyright: 2010 tipfy.org.
    :copyright: 2009 Plurk Inc.
    :license: BSD, see LICENSE.txt for more details.
"""
from google.appengine.api import urlfetch

from werkzeug import url_encode

from wtforms.validators import *
from wtforms.validators import ValidationError

from tipfy import Tipfy, get_config


RECAPTCHA_VERIFY_SERVER = 'http://api-verify.recaptcha.net/verify'


class CsrfToken(object):
    """
    Compares the incoming data to a sequence of valid inputs.

    :param values:
        A sequence of valid inputs.
    :param message:
        Error message to raise in case of a validation error.
    """
    def __init__(self, values, message=None):
        self.values = values
        self.message = message

    def __call__(self, form, field):
        if field.csrf_token:
            if field.csrf_token not in self.values:
                if self.message is None:
                    #self.message = field.gettext(u'The form expired.')
                    self.message = 'The form expired.'

                raise ValueError(self.message)
            else:
                self.values.remove(field.csrf_token)


class Recaptcha(object):
    """Validates a ReCaptcha."""
    _error_codes = {
        'invalid-site-public-key': 'The public key for reCAPTCHA is invalid',
        'invalid-site-private-key': 'The private key for reCAPTCHA is invalid',
        'invalid-referrer': 'The public key for reCAPTCHA is not valid for '
            'this domainin',
        'verify-params-incorrect': 'The parameters passed to reCAPTCHA '
            'verification are incorrect',
    }

    def __init__(self, message=u'Invalid word. Please try again.'):
        self.message = message

    def __call__(self, form, field):
        request = Tipfy.request
        challenge = request.form.get('recaptcha_challenge_field', '')
        response = request.form.get('recaptcha_response_field', '')
        remote_ip = request.remote_addr

        if not challenge or not response:
            raise ValidationError('This field is required.')

        if not self._validate_recaptcha(challenge, response, remote_ip):
            field.recaptcha_error = 'incorrect-captcha-sol'
            raise ValidationError(self.message)

    def _validate_recaptcha(self, challenge, response, remote_addr):
        """Performs the actual validation."""
        private_key = get_config('tipfy.ext.wtforms', 'recaptcha_private_key')
        result = urlfetch.fetch(url=RECAPTCHA_VERIFY_SERVER,
            method=urlfetch.POST,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            payload=url_encode({
                'privatekey': private_key,
                'remoteip':   remote_addr,
                'challenge':  challenge,
                'response':   response
            }))

        if result.status_code != 200:
            return False

        rv = [l.strip() for l in result.content.splitlines()]

        if rv and rv[0] == 'true':
            return True

        if len(rv) > 1:
            error = rv[1]
            if error in self._error_codes:
                raise RuntimeError(self._error_codes[error])

        return False
