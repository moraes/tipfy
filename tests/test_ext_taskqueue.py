# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.taskqueue
"""
import unittest

from google.appengine.api.labs import taskqueue
from google.appengine.ext import db
from gaetestbed import DataStoreTestCase, TaskQueueTestCase

import _base

from tipfy import url_for, Rule
import tipfy

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
    def tearDown(self):
        tipfy.local_manager.cleanup()
