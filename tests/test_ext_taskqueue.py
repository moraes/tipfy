# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.taskqueue
"""
import sys
import unittest
import hashlib

from google.appengine.api.labs import taskqueue
from google.appengine.ext import db
from gaetestbed import DataStoreTestCase, TaskQueueTestCase

from _base import get_app, get_environ, get_request
from tipfy import url_for


def get_rules():
    # Fake get_rules() for testing.
    from tipfy import Rule
    return [
        Rule('/_tasks/process-mymodel/', endpoint='tasks/process-mymodel',
            handler='%s.FooModelEntityTaskHandler' % __name__),
        Rule('/_tasks/process-mymodel/<string:key>', endpoint='tasks/process-mymodel',
            handler='%s.FooModelEntityTaskHandler' % __name__),
    ]


class FooModel(db.Model):
    number = db.IntegerProperty()


class TestTasks(DataStoreTestCase, TaskQueueTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        TaskQueueTestCase.setUp(self)
        # Make it load our test url rules.
        sys.modules['urls'] = sys.modules[__name__]

        # Setup app
        app = get_app()
        environ = get_environ()
        request = get_request(environ)
        app.url_adapter = app.url_map.bind_to_environ(environ)

    def tearDown(self):
        if 'urls' in sys.modules:
            del sys.modules['urls']

    def test_entity_task_handler(self):
        # Create 10 entities.
        db.put([FooModel(number=n) for n in range(0, 10)])

        """
        # unfinished stuff
        url = url_for('tasks/process-mymodel')
        taskqueue.add(url=url)
        self.assertTasksInQueue(url=url)
        """
