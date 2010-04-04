# -*- coding: utf-8 -*-
"""
    shorty
    ~~~~~~

    URL shortner example app, ported from Werkzeug's "Shorty" example.

    :copyright: (c) 2010 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from urlparse import urlparse

from tipfy import (NotFound, redirect, redirect_to, request, RequestHandler,
    url_for)
from tipfy.ext.jinja2 import render_response

from apps.shorty.models import Url, url_pager


ALLOWED_SCHEMES = frozenset(['http', 'https', 'ftp', 'ftps'])


def validate_url(url):
    return urlparse(url)[0] in ALLOWED_SCHEMES


class NewUrlHandler(RequestHandler):
    error = None
    url = None

    def get(self, **kwargs):
        context = {
            'error': self.error or '',
            'url': self.url or '',
        }
        return render_response('shorty/new.html', **context)

    def post(self, **kwargs):
        self.url = request.form.get('url')
        name = request.form.get('alias')
        public = 'private' not in request.form

        if not validate_url(self.url):
            self.error = "I'm sorry but you cannot shorten this URL."
        elif name:
            if len(name) > 140:
                self.error = 'Your alias is too long.'
            elif '/' in name:
                self.error = 'Your alias might not include a slash.'

        if not self.error:
            url_name = Url.create(self.url, name=name, public=public)
            if not url_name:
                self.error = 'The alias you have requested exists already.'
            else:
                return redirect_to('shorty/view', url_name=url_name)

        return self.get()


class ViewUrlHandler(RequestHandler):
    def get(self, **kwargs):
        url = Url.get_by_key_name(kwargs.get('url_name'))
        if not url:
            raise NotFound()

        return render_response('shorty/display.html', url=url)


class LinkHandler(RequestHandler):
    def get(self, **kwargs):
        url = Url.get_by_key_name(kwargs.get('url_name'))
        if not url:
            raise NotFound()

        return redirect(url.target, 301)


class ListHandler(RequestHandler):
    def get(self, **kwargs):
        urls, cursor = url_pager(kwargs.get('cursor', None))
        return render_response('shorty/list.html', urls=urls, cursor=cursor)
