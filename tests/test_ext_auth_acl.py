# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.user.acl
"""
import unittest

from nose.tools import assert_raises
from gaetestbed import DataStoreTestCase, MemcacheTestCase

from google.appengine.api import memcache

import _base

import tipfy
from tipfy.ext.auth.acl import Acl, AclRules, _rules_map, AclMixin


class TestAcl(DataStoreTestCase, MemcacheTestCase, unittest.TestCase):
    def setUp(self):
        # Clean up datastore.
        super(TestAcl, self).setUp()

        tipfy.local_manager.cleanup()

        self.app = tipfy.WSGIApplication()
        self.app.config['tipfy']['dev'] = False

        Acl.roles_map = {}
        Acl.roles_lock = self.app.config.get('tipfy', 'version_id')
        _rules_map.clear()

    def tearDown(self):
        tipfy.local_manager.cleanup()
        self.app.config['tipfy']['dev'] = True

        Acl.roles_map = {}
        Acl.roles_lock = self.app.config.get('tipfy', 'version_id')
        _rules_map.clear()

    def test_test_insert_or_update(self):
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        assert user_acl is None

        # Set empty rules.
        user_acl = AclRules.insert_or_update(area='test', user='test')
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        assert user_acl is not None
        assert user_acl.rules == []
        assert user_acl.roles == []

        rules = [
            ('topic_1', 'name_1', True),
            ('topic_1', 'name_2', True),
            ('topic_2', 'name_1', False),
        ]

        user_acl = AclRules.insert_or_update(area='test', user='test', rules=rules)
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        assert user_acl is not None
        assert user_acl.rules == rules
        assert user_acl.roles == []

        extra_rule = ('topic_3', 'name_3', True)
        rules.append(extra_rule)

        user_acl = AclRules.insert_or_update(area='test', user='test', rules=rules, roles=['foo', 'bar', 'baz'])
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        assert user_acl is not None
        assert user_acl.rules == rules
        assert user_acl.roles == ['foo', 'bar', 'baz']

    def test_set_rules(self):
        """Test setting and appending rules."""
        rules = [
            ('topic_1', 'name_1', True),
            ('topic_1', 'name_2', True),
            ('topic_2', 'name_1', False),
        ]
        extra_rule = ('topic_3', 'name_3', True)

        # Set empty rules.
        user_acl = AclRules.insert_or_update(area='test', user='test')

        # Set rules and save the record.
        user_acl = AclRules.insert_or_update(area='test', user='test', rules=rules)

        # Fetch the record again, and compare.
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        assert user_acl.rules == rules

        # Append more rules.
        user_acl.rules.append(extra_rule)
        user_acl.put()
        rules.append(extra_rule)

        # Fetch the record again, and compare.
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        assert user_acl.rules == rules

    def test_delete_rules(self):
        rules = [
            ('topic_1', 'name_1', True),
            ('topic_1', 'name_2', True),
            ('topic_2', 'name_1', False),
        ]
        user_acl = AclRules.insert_or_update(area='test', user='test', rules=rules)

        # Fetch the record again, and compare.
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        assert user_acl.rules == rules

        key_name = AclRules.get_key_name('test', 'test')
        acl = Acl('test', 'test')

        cached = memcache.get(key_name, namespace=AclRules.__name__)
        assert key_name in _rules_map
        assert cached == _rules_map[key_name]

        user_acl.delete()
        user_acl2 = AclRules.get_by_area_and_user('test', 'test')

        cached = memcache.get(key_name, namespace=AclRules.__name__)
        assert user_acl2 is None
        assert key_name not in _rules_map
        assert cached is None

    def test_is_rule_set(self):
        rules = [
            ('topic_1', 'name_1', True),
            ('topic_1', 'name_2', True),
            ('topic_2', 'name_1', False),
        ]
        user_acl = AclRules.insert_or_update(area='test', user='test', rules=rules)

        # Fetch the record again, and compare.
        user_acl = AclRules.get_by_area_and_user('test', 'test')

        assert user_acl.is_rule_set(*rules[0]) is True
        assert user_acl.is_rule_set(*rules[1]) is True
        assert user_acl.is_rule_set(*rules[2]) is True
        assert user_acl.is_rule_set('topic_1', 'name_3', True) is False

    def test_no_area_or_no_user(self):
        acl1 = Acl('foo', None)
        acl2 = Acl(None, 'foo')

        assert acl1.has_any_access() is False
        assert acl2.has_any_access() is False

    def test_default_roles_lock(self):
        Acl.roles_lock = None
        acl2 = Acl('foo', 'foo')

        assert acl2.roles_lock == self.app.config.get('tipfy', 'version_id')

    def test_set_invalid_rules(self):
        rules = {}
        assert_raises(AssertionError, AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = ['foo', 'bar', True]
        assert_raises(AssertionError, AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = [('foo',)]
        assert_raises(AssertionError, AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = [('foo', 'bar')]
        assert_raises(AssertionError, AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = [(1, 2, 3)]
        assert_raises(AssertionError, AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = [('foo', 'bar', True)]
        AclRules.insert_or_update(area='test', user='test', rules=rules)
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        user_acl.rules.append((1, 2, 3))
        assert_raises(AssertionError, user_acl.put)

    def test_example(self):
        """Tests the example set in the acl module."""
        # Set a dict of roles with an 'admin' role that has full access and assign
        # users to it. Each role maps to a list of rules. Each rule is a tuple
        # (topic, name, flag), where flag is as bool to allow or disallow access.
        # Wildcard '*' can be used to match all topics and/or names.
        Acl.roles_map = {
            'admin': [
                ('*', '*', True),
            ],
        }

        # Assign users 'user_1' and 'user_2' to the 'admin' role.
        AclRules.insert_or_update(area='my_area', user='user_1', roles=['admin'])
        AclRules.insert_or_update(area='my_area', user='user_2', roles=['admin'])

        # Restrict 'user_2' from accessing a specific resource, adding a new rule
        # with flag set to False. Now this user has access to everything except this
        # resource.
        user_acl = AclRules.get_by_area_and_user('my_area', 'user_2')
        user_acl.rules.append(('UserAdmin', '*', False))
        user_acl.put()

        # Check 'user_2' permission.
        acl = Acl(area='my_area', user='user_2')
        assert acl.has_access(topic='UserAdmin', name='save') is False
        assert acl.has_access(topic='UserAdmin', name='get') is False
        assert acl.has_access(topic='AnythingElse', name='put') is True

    def test_is_one(self):
        AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor', 'designer'])

        acl = Acl(area='my_area', user='user_1')
        assert acl.is_one('editor') is True
        assert acl.is_one('designer') is True
        assert acl.is_one('admin') is False

    def test_is_any(self):
        AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor', 'designer'])

        acl = Acl(area='my_area', user='user_1')
        assert acl.is_any(['editor', 'admin']) is True
        assert acl.is_any(['admin', 'designer']) is True
        assert acl.is_any(['admin', 'user']) is False

    def test_is_all(self):
        AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor', 'designer'])

        acl = Acl(area='my_area', user='user_1')
        assert acl.is_all(['editor', 'admin']) is False
        assert acl.is_all(['admin', 'designer']) is False
        assert acl.is_all(['admin', 'user']) is False
        assert acl.is_all(['editor', 'designer']) is True

    def test_non_existent_user(self):
        acl = Acl(area='my_area', user='user_3')
        assert acl.has_any_access() is False

    def test_has_any_access(self):
        AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor', 'designer'])
        AclRules.insert_or_update(area='my_area', user='user_2', rules=[('*', '*', True)])
        AclRules.insert_or_update(area='my_area', user='user_3')

        acl = Acl(area='my_area', user='user_1')
        assert acl.has_any_access() is True

        acl = Acl(area='my_area', user='user_2')
        assert acl.has_any_access() is True

        acl = Acl(area='my_area', user='user_3')
        assert acl.has_any_access() is False
        assert acl._rules == []
        assert acl._roles == []

    def test_has_access_invalid_parameters(self):
        AclRules.insert_or_update(area='my_area', user='user_1', rules=[('*', '*', True)])

        acl1 = Acl(area='my_area', user='user_1')

        assert_raises(ValueError, acl1.has_access, 'content', '*')
        assert_raises(ValueError, acl1.has_access, '*', 'content')

    def test_has_access(self):
        AclRules.insert_or_update(area='my_area', user='user_1', rules=[('*', '*', True)])
        AclRules.insert_or_update(area='my_area', user='user_2', rules=[('content', '*', True), ('content', 'delete', False)])
        AclRules.insert_or_update(area='my_area', user='user_3', rules=[('content', 'read', True)])

        acl1 = Acl(area='my_area', user='user_1')
        acl2 = Acl(area='my_area', user='user_2')
        acl3 = Acl(area='my_area', user='user_3')

        assert acl1.has_access('content', 'read') is True
        assert acl1.has_access('content', 'update') is True
        assert acl1.has_access('content', 'delete') is True

        assert acl2.has_access('content', 'read') is True
        assert acl2.has_access('content', 'update') is True
        assert acl2.has_access('content', 'delete') is False

        assert acl3.has_access('content', 'read') is True
        assert acl3.has_access('content', 'update') is False
        assert acl3.has_access('content', 'delete') is False

    def test_has_access_with_roles(self):
        Acl.roles_map = {
            'admin':       [('*', '*', True),],
            'editor':      [('content', '*', True),],
            'contributor': [('content', '*', True), ('content', 'delete', False)],
            'designer':    [('design', '*', True),],
        }

        AclRules.insert_or_update(area='my_area', user='user_1', roles=['admin'])
        acl1 = Acl(area='my_area', user='user_1')

        AclRules.insert_or_update(area='my_area', user='user_2', roles=['admin'], rules=[('ManageUsers', '*', False)])
        acl2 = Acl(area='my_area', user='user_2')

        AclRules.insert_or_update(area='my_area', user='user_3', roles=['editor'])
        acl3 = Acl(area='my_area', user='user_3')

        AclRules.insert_or_update(area='my_area', user='user_4', roles=['contributor'], rules=[('design', '*', True),])
        acl4 = Acl(area='my_area', user='user_4')

        assert acl1.has_access('ApproveUsers', 'save') is True
        assert acl1.has_access('ManageUsers', 'edit') is True
        assert acl1.has_access('ManageUsers', 'delete') is True

        assert acl1.has_access('ApproveUsers', 'save') is True
        assert acl2.has_access('ManageUsers', 'edit') is False
        assert acl2.has_access('ManageUsers', 'delete') is False

        assert acl3.has_access('ApproveUsers', 'save') is False
        assert acl3.has_access('ManageUsers', 'edit') is False
        assert acl3.has_access('ManageUsers', 'delete') is False
        assert acl3.has_access('content', 'edit') is True
        assert acl3.has_access('content', 'delete') is True
        assert acl3.has_access('content', 'save') is True
        assert acl3.has_access('design', 'edit') is False
        assert acl3.has_access('design', 'delete') is False

        assert acl4.has_access('ApproveUsers', 'save') is False
        assert acl4.has_access('ManageUsers', 'edit') is False
        assert acl4.has_access('ManageUsers', 'delete') is False
        assert acl4.has_access('content', 'edit') is True
        assert acl4.has_access('content', 'delete') is False
        assert acl4.has_access('content', 'save') is True
        assert acl4.has_access('design', 'edit') is True
        assert acl4.has_access('design', 'delete') is True

    def test_roles_lock_unchanged(self):
        roles_map1 = {
            'editor':      [('content', '*', True),],
            'contributor': [('content', '*', True), ('content', 'delete', False)],
        }
        Acl.roles_map = roles_map1
        Acl.roles_lock = 'initial'

        AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor'])
        acl1 = Acl(area='my_area', user='user_1')

        AclRules.insert_or_update(area='my_area', user='user_2', roles=['contributor'])
        acl2 = Acl(area='my_area', user='user_2')

        assert acl1.has_access('content', 'add') is True
        assert acl1.has_access('content', 'edit') is True
        assert acl1.has_access('content', 'delete') is True

        assert acl2.has_access('content', 'add') is True
        assert acl2.has_access('content', 'edit') is True
        assert acl2.has_access('content', 'delete') is False

        roles_map2 = {
            'editor':      [('content', '*', True),],
            'contributor': [('content', '*', True), ('content', 'delete', False), ('content', 'add', False)],
        }
        Acl.roles_map = roles_map2
        # Don't change the lock to check that the cache will be kept.
        # Acl.roles_lock = 'changed'

        acl1 = Acl(area='my_area', user='user_1')
        acl2 = Acl(area='my_area', user='user_2')

        assert acl1.has_access('content', 'add') is True
        assert acl1.has_access('content', 'edit') is True
        assert acl1.has_access('content', 'delete') is True

        assert acl2.has_access('content', 'add') is True
        assert acl2.has_access('content', 'edit') is True
        assert acl2.has_access('content', 'delete') is False

    def test_roles_lock_changed(self):
        roles_map1 = {
            'editor':      [('content', '*', True),],
            'contributor': [('content', '*', True), ('content', 'delete', False)],
        }
        Acl.roles_map = roles_map1
        Acl.roles_lock = 'initial'

        AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor'])
        acl1 = Acl(area='my_area', user='user_1')

        AclRules.insert_or_update(area='my_area', user='user_2', roles=['contributor'])
        acl2 = Acl(area='my_area', user='user_2')

        assert acl1.has_access('content', 'add') is True
        assert acl1.has_access('content', 'edit') is True
        assert acl1.has_access('content', 'delete') is True

        assert acl2.has_access('content', 'add') is True
        assert acl2.has_access('content', 'edit') is True
        assert acl2.has_access('content', 'delete') is False

        roles_map2 = {
            'editor':      [('content', '*', True),],
            'contributor': [('content', '*', True), ('content', 'delete', False), ('content', 'add', False)],
        }
        Acl.roles_map = roles_map2
        Acl.roles_lock = 'changed'

        acl1 = Acl(area='my_area', user='user_1')
        acl2 = Acl(area='my_area', user='user_2')

        assert acl1.has_access('content', 'add') is True
        assert acl1.has_access('content', 'edit') is True
        assert acl1.has_access('content', 'delete') is True

        assert acl2.has_access('content', 'add') is False
        assert acl2.has_access('content', 'edit') is True
        assert acl2.has_access('content', 'delete') is False

    def test_acl_mixin(self):
        roles_map1 = {
            'editor':      [('content', '*', True),],
            'contributor': [('content', '*', True), ('content', 'delete', False)],
        }
        AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor'])

        class Area(object):
            def key(self):
                return 'my_area'

        class User(object):
            def key(self):
                return 'user_1'

        class MyHandler(AclMixin):
            roles_map = roles_map1
            roles_lock = 'foo'

            def __init__(self):
                self.area = Area()
                self.current_user = User()

        handler = MyHandler()
        assert handler.acl.has_access('content', 'add') is True
        assert handler.acl.has_access('content', 'edit') is True
        assert handler.acl.has_access('content', 'delete') is True
        assert handler.acl.has_access('foo', 'delete') is False
