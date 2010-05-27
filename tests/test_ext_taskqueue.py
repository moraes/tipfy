# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.taskqueue
"""
import time
import unittest

from google.appengine.ext import deferred

from google.appengine.api.labs import taskqueue
from google.appengine.ext import db
from gaetestbed import DataStoreTestCase, TaskQueueTestCase

import _base

from tipfy import Rule, url_for, Tipfy


def get_rules():
    # Fake get_rules() for testing.
    return [
        Rule('/_tasks/process-mymodel/', endpoint='tasks/process-mymodel',
            handler='%s.FooModelEntityTaskHandler' % __name__),
        Rule('/_tasks/process-mymodel/<string:key>', endpoint='tasks/process-mymodel',
            handler='%s.FooModelEntityTaskHandler' % __name__),
    ]


def get_url_map():
    # Fake get_rules() for testing.
    rules = [
        Rule('/_ah/queue/deferred', endpoint='tasks/deferred', handler='tipfy.ext.taskqueue:DeferredHandler'),
    ]

    return Map(rules)


def get_app():
    return Tipfy({
        'tipfy': {
            'url_map': get_url_map(),
            'dev': True,
        },
    })


class FooModel(db.Model):
    number = db.IntegerProperty()


def save_entities(numbers):
    entities = []
    for number in numbers:
        entities.append(FooModel(key_name=str(number), number=number))

    res = db.put(entities)

    import sys
    sys.exit(res)


class TestDeferredHandler(DataStoreTestCase, TaskQueueTestCase, unittest.TestCase):
    """TODO"""
    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_simple_deferred(self):
        numbers = [1234, 1577, 988]
        keys = [db.Key.from_path('FooModel', str(number)) for number in numbers]
        entities = db.get(keys)
        assert entities == [None, None, None]

        deferred.defer(save_entities, numbers)
        #self.assertTasksInQueue()
        #time.sleep(3)

        #entities = db.get(keys)
        #assert entities == [None, None, None]


class TestTasks(DataStoreTestCase, TaskQueueTestCase, unittest.TestCase):
    """TODO"""
    def tearDown(self):
        Tipfy.app = Tipfy.request = None
