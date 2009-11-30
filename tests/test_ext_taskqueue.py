# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.taskqueue
"""
import unittest

from google.appengine.api.labs import taskqueue
from google.appengine.ext import db
from gaetestbed import DataStoreTestCase, TaskQueueTestCase

from _base import get_app, get_environ, get_request
from tipfy import url_for, Rule


def get_rules():
    # Fake get_rules() for testing.
    return [
        Rule('/_tasks/process-mymodel/', endpoint='tasks/process-mymodel',
            handler='%s.FooModelEntityTaskHandler' % __name__),
        Rule('/_tasks/process-mymodel/<string:key>', endpoint='tasks/process-mymodel',
            handler='%s.FooModelEntityTaskHandler' % __name__),
    ]


class FooModel(db.Model):
    number = db.IntegerProperty()


class TestTasks(DataStoreTestCase, TaskQueueTestCase, unittest.TestCase):
    """TODO"""
