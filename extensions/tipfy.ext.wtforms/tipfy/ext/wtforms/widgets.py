# -*- coding: utf-8 -*-
"""
    tipfy.ext.wtforms.widgets
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Form widgets.

    :copyright: 2010 WTForms authors.
    :copyright: 2010 tipfy.org.
    :copyright: 2009 Plurk Inc.
    :license: BSD, see LICENSE.txt for more details.
"""
from werkzeug import url_encode

from django.utils.simplejson import dumps

from wtforms.widgets import *

from tipfy import get_config
try:
    from tipfy.ext.i18n import _
except ImportError, e:
    _ = lambda string: string


RECAPTCHA_API_SERVER = 'http://api.recaptcha.net/'
RECAPTCHA_SSL_API_SERVER = 'https://api-secure.recaptcha.net/'
RECAPTCHA_HTML = u'''
<script type="text/javascript">var RecaptchaOptions = %(options)s;</script>
<script type="text/javascript" src="%(script_url)s"></script>
<noscript>
  <div><iframe src="%(frame_url)s" height="300" width="500"></iframe></div>
  <div><textarea name="recaptcha_challenge_field" rows="3" cols="40"></textarea>
  <input type="hidden" name="recaptcha_response_field" value="manual_challenge"></div>
</noscript>
'''

class RecaptchaWidget(object):
    def __call__(self, field, error=None, **kwargs):
        """Returns the recaptcha input HTML."""
        if get_config('tipfy.ext.wtforms', 'recaptcha_use_ssl'):
            server = RECAPTCHA_SSL_API_SERVER
        else:
            server = RECAPTCHA_API_SERVER

        query_options = dict(k=get_config('tipfy.ext.wtforms',
            'recaptcha_public_key'))

        if field.recaptcha_error is not None:
            query_options['error'] = unicode(field.recaptcha_error)

        query = url_encode(query_options)

        # Widget default options.
        options = {
            'theme': 'clean',
            'custom_translations': {
                'visual_challenge':    _('Get a visual challenge'),
                'audio_challenge':     _('Get an audio challenge'),
                'refresh_btn':         _('Get a new challenge'),
                'instructions_visual': _('Type the two words:'),
                'instructions_audio':  _('Type what you hear:'),
                'help_btn':            _('Help'),
                'play_again':          _('Play sound again'),
                'cant_hear_this':      _('Download sound as MP3'),
                'incorrect_try_again': _('Incorrect. Try again.'),
            }
        }
        custom_options = get_config('tipfy.ext.wtforms', 'recaptcha_options')
        if custom_options:
            options.update(custom_options)

        return RECAPTCHA_HTML % dict(
            script_url='%schallenge?%s' % (server, query),
            frame_url='%snoscript?%s' % (server, query),
            options=dumps(options)
        )
