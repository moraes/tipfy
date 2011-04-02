# -*- coding: utf-8 -*-
"""
	Tests for tipfyext.appenginetaskqueue
"""
import time
import unittest

from google.appengine.ext import deferred

from google.appengine.api import taskqueue
from google.appengine.ext import db

from tipfy import Rule, Tipfy
from tipfy.app import local

import test_utils


def get_rules():
	# Fake get_rules() for testing.
	return [
		Rule('/_tasks/process-mymodel/', name='tasks/process-mymodel',
			handler='%s.TaskTestModelEntityTaskHandler' % __name__),
		Rule('/_tasks/process-mymodel/<string:key>', name='tasks/process-mymodel',
			handler='%s.TaskTestModelEntityTaskHandler' % __name__),
	]


def get_url_rules():
	# Fake get_rules() for testing.
	rules = [
		Rule('/_ah/queue/deferred', name='tasks/deferred', handler='tipfy.appengine.taskqueue.DeferredHandler'),
	]

	return Map(rules)


def get_app():
	return Tipfy({
		'tipfy': {
			'dev': True,
		},
	}, rules=get_url_rules())


class TaskTestModel(db.Model):
	number = db.IntegerProperty()


def save_entities(numbers):
	entities = []
	for number in numbers:
		entities.append(TaskTestModel(key_name=str(number), number=number))

	res = db.put(entities)

	import sys
	sys.exit(res)


class TestDeferredHandler(test_utils.BaseTestCase):
	"""TODO"""

	def test_simple_deferred(self):
		numbers = [1234, 1577, 988]
		keys = [db.Key.from_path('TaskTestModel', str(number)) for number in numbers]
		entities = db.get(keys)
		self.assertEqual(entities, [None, None, None])

		deferred.defer(save_entities, numbers)


class TestTasks(test_utils.BaseTestCase):
	"""TODO"""


if __name__ == '__main__':
	test_utils.main()
