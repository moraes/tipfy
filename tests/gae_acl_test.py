# -*- coding: utf-8 -*-
"""
    Tests for tipfy.appengine.acl
"""
import unittest

from google.appengine.api import memcache

from tipfy import Tipfy, Request, RequestHandler, CURRENT_VERSION_ID
from tipfy.app import local
from tipfy.appengine.acl import Acl, AclRules, _rules_map, AclMixin

from tipfy.app import local

import test_utils


class TestAcl(test_utils.BaseTestCase):
    def setUp(self):
        # Clean up datastore.
        super(TestAcl, self).setUp()

        self.app = Tipfy()
        self.app.config['tipfy']['dev'] = False
        local.request = Request.from_values()
        local.request.app = self.app

        Acl.roles_map = {}
        Acl.roles_lock = CURRENT_VERSION_ID
        _rules_map.clear()
        test_utils.BaseTestCase.setUp(self)

    def tearDown(self):
        self.app.config['tipfy']['dev'] = True

        Acl.roles_map = {}
        Acl.roles_lock = CURRENT_VERSION_ID
        _rules_map.clear()
        test_utils.BaseTestCase.tearDown(self)

    def test_test_insert_or_update(self):
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        self.assertEqual(user_acl, None)

        # Set empty rules.
        user_acl = AclRules.insert_or_update(area='test', user='test')
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        self.assertNotEqual(user_acl, None)
        self.assertEqual(user_acl.rules, [])
        self.assertEqual(user_acl.roles, [])

        rules = [
            ('topic_1', 'name_1', True),
            ('topic_1', 'name_2', True),
            ('topic_2', 'name_1', False),
        ]

        user_acl = AclRules.insert_or_update(area='test', user='test', rules=rules)
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        self.assertNotEqual(user_acl, None)
        self.assertEqual(user_acl.rules, rules)
        self.assertEqual(user_acl.roles, [])

        extra_rule = ('topic_3', 'name_3', True)
        rules.append(extra_rule)

        user_acl = AclRules.insert_or_update(area='test', user='test', rules=rules, roles=['foo', 'bar', 'baz'])
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        self.assertNotEqual(user_acl, None)
        self.assertEqual(user_acl.rules, rules)
        self.assertEqual(user_acl.roles, ['foo', 'bar', 'baz'])

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
        self.assertEqual(user_acl.rules, rules)

        # Append more rules.
        user_acl.rules.append(extra_rule)
        user_acl.put()
        rules.append(extra_rule)

        # Fetch the record again, and compare.
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        self.assertEqual(user_acl.rules, rules)

    def test_delete_rules(self):
        rules = [
            ('topic_1', 'name_1', True),
            ('topic_1', 'name_2', True),
            ('topic_2', 'name_1', False),
        ]
        user_acl = AclRules.insert_or_update(area='test', user='test', rules=rules)

        # Fetch the record again, and compare.
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        self.assertEqual(user_acl.rules, rules)

        key_name = AclRules.get_key_name('test', 'test')
        acl = Acl('test', 'test')

        cached = memcache.get(key_name, namespace=AclRules.__name__)
        self.assertEqual(key_name in _rules_map, True)
        self.assertEqual(cached, _rules_map[key_name])

        user_acl.delete()
        user_acl2 = AclRules.get_by_area_and_user('test', 'test')

        cached = memcache.get(key_name, namespace=AclRules.__name__)
        self.assertEqual(user_acl2, None)
        self.assertEqual(key_name not in _rules_map, True)
        self.assertEqual(cached, None)

    def test_is_rule_set(self):
        rules = [
            ('topic_1', 'name_1', True),
            ('topic_1', 'name_2', True),
            ('topic_2', 'name_1', False),
        ]
        user_acl = AclRules.insert_or_update(area='test', user='test', rules=rules)

        # Fetch the record again, and compare.
        user_acl = AclRules.get_by_area_and_user('test', 'test')

        self.assertEqual(user_acl.is_rule_set(*rules[0]), True)
        self.assertEqual(user_acl.is_rule_set(*rules[1]), True)
        self.assertEqual(user_acl.is_rule_set(*rules[2]), True)
        self.assertEqual(user_acl.is_rule_set('topic_1', 'name_3', True), False)

    def test_no_area_or_no_user(self):
        acl1 = Acl('foo', None)
        acl2 = Acl(None, 'foo')

        self.assertEqual(acl1.has_any_access(), False)
        self.assertEqual(acl2.has_any_access(), False)

    def test_default_roles_lock(self):
        Acl.roles_lock = None
        acl2 = Acl('foo', 'foo')

        self.assertEqual(acl2.roles_lock, CURRENT_VERSION_ID)

    def test_set_invalid_rules(self):
        rules = {}
        self.assertRaises(AssertionError, AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = ['foo', 'bar', True]
        self.assertRaises(AssertionError, AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = [('foo',)]
        self.assertRaises(AssertionError, AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = [('foo', 'bar')]
        self.assertRaises(AssertionError, AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = [(1, 2, 3)]
        self.assertRaises(AssertionError, AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = [('foo', 'bar', True)]
        AclRules.insert_or_update(area='test', user='test', rules=rules)
        user_acl = AclRules.get_by_area_and_user('test', 'test')
        user_acl.rules.append((1, 2, 3))
        self.assertRaises(AssertionError, user_acl.put)

    def test_example(self):
        """Tests the example set in the acl module."""
        # Set a dict of roles with an 'admin' role that has full access and assign
        # users to it. Each role maps to a list of rules. Each rule, a tuple
        # (topic, name, flag), where flag, as bool to allow or disallow access.
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
        self.assertEqual(acl.has_access(topic='UserAdmin', name='save'), False)
        self.assertEqual(acl.has_access(topic='UserAdmin', name='get'), False)
        self.assertEqual(acl.has_access(topic='AnythingElse', name='put'), True)

    def test_is_one(self):
        AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor', 'designer'])

        acl = Acl(area='my_area', user='user_1')
        self.assertEqual(acl.is_one('editor'), True)
        self.assertEqual(acl.is_one('designer'), True)
        self.assertEqual(acl.is_one('admin'), False)

    def test_is_any(self):
        AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor', 'designer'])

        acl = Acl(area='my_area', user='user_1')
        self.assertEqual(acl.is_any(['editor', 'admin']), True)
        self.assertEqual(acl.is_any(['admin', 'designer']), True)
        self.assertEqual(acl.is_any(['admin', 'user']), False)

    def test_is_all(self):
        AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor', 'designer'])

        acl = Acl(area='my_area', user='user_1')
        self.assertEqual(acl.is_all(['editor', 'admin']), False)
        self.assertEqual(acl.is_all(['admin', 'designer']), False)
        self.assertEqual(acl.is_all(['admin', 'user']), False)
        self.assertEqual(acl.is_all(['editor', 'designer']), True)

    def test_non_existent_user(self):
        acl = Acl(area='my_area', user='user_3')
        self.assertEqual(acl.has_any_access(), False)

    def test_has_any_access(self):
        AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor', 'designer'])
        AclRules.insert_or_update(area='my_area', user='user_2', rules=[('*', '*', True)])
        AclRules.insert_or_update(area='my_area', user='user_3')

        acl = Acl(area='my_area', user='user_1')
        self.assertEqual(acl.has_any_access(), True)

        acl = Acl(area='my_area', user='user_2')
        self.assertEqual(acl.has_any_access(), True)

        acl = Acl(area='my_area', user='user_3')
        self.assertEqual(acl.has_any_access(), False)
        self.assertEqual(acl._rules, [])
        self.assertEqual(acl._roles, [])

    def test_has_access_invalid_parameters(self):
        AclRules.insert_or_update(area='my_area', user='user_1', rules=[('*', '*', True)])

        acl1 = Acl(area='my_area', user='user_1')

        self.assertRaises(ValueError, acl1.has_access, 'content', '*')
        self.assertRaises(ValueError, acl1.has_access, '*', 'content')

    def test_has_access(self):
        AclRules.insert_or_update(area='my_area', user='user_1', rules=[('*', '*', True)])
        AclRules.insert_or_update(area='my_area', user='user_2', rules=[('content', '*', True), ('content', 'delete', False)])
        AclRules.insert_or_update(area='my_area', user='user_3', rules=[('content', 'read', True)])

        acl1 = Acl(area='my_area', user='user_1')
        acl2 = Acl(area='my_area', user='user_2')
        acl3 = Acl(area='my_area', user='user_3')

        self.assertEqual(acl1.has_access('content', 'read'), True)
        self.assertEqual(acl1.has_access('content', 'update'), True)
        self.assertEqual(acl1.has_access('content', 'delete'), True)

        self.assertEqual(acl2.has_access('content', 'read'), True)
        self.assertEqual(acl2.has_access('content', 'update'), True)
        self.assertEqual(acl2.has_access('content', 'delete'), False)

        self.assertEqual(acl3.has_access('content', 'read'), True)
        self.assertEqual(acl3.has_access('content', 'update'), False)
        self.assertEqual(acl3.has_access('content', 'delete'), False)

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

        self.assertEqual(acl1.has_access('ApproveUsers', 'save'), True)
        self.assertEqual(acl1.has_access('ManageUsers', 'edit'), True)
        self.assertEqual(acl1.has_access('ManageUsers', 'delete'), True)

        self.assertEqual(acl1.has_access('ApproveUsers', 'save'), True)
        self.assertEqual(acl2.has_access('ManageUsers', 'edit'), False)
        self.assertEqual(acl2.has_access('ManageUsers', 'delete'), False)

        self.assertEqual(acl3.has_access('ApproveUsers', 'save'), False)
        self.assertEqual(acl3.has_access('ManageUsers', 'edit'), False)
        self.assertEqual(acl3.has_access('ManageUsers', 'delete'), False)
        self.assertEqual(acl3.has_access('content', 'edit'), True)
        self.assertEqual(acl3.has_access('content', 'delete'), True)
        self.assertEqual(acl3.has_access('content', 'save'), True)
        self.assertEqual(acl3.has_access('design', 'edit'), False)
        self.assertEqual(acl3.has_access('design', 'delete'), False)

        self.assertEqual(acl4.has_access('ApproveUsers', 'save'), False)
        self.assertEqual(acl4.has_access('ManageUsers', 'edit'), False)
        self.assertEqual(acl4.has_access('ManageUsers', 'delete'), False)
        self.assertEqual(acl4.has_access('content', 'edit'), True)
        self.assertEqual(acl4.has_access('content', 'delete'), False)
        self.assertEqual(acl4.has_access('content', 'save'), True)
        self.assertEqual(acl4.has_access('design', 'edit'), True)
        self.assertEqual(acl4.has_access('design', 'delete'), True)

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

        self.assertEqual(acl1.has_access('content', 'add'), True)
        self.assertEqual(acl1.has_access('content', 'edit'), True)
        self.assertEqual(acl1.has_access('content', 'delete'), True)

        self.assertEqual(acl2.has_access('content', 'add'), True)
        self.assertEqual(acl2.has_access('content', 'edit'), True)
        self.assertEqual(acl2.has_access('content', 'delete'), False)

        roles_map2 = {
            'editor':      [('content', '*', True),],
            'contributor': [('content', '*', True), ('content', 'delete', False), ('content', 'add', False)],
        }
        Acl.roles_map = roles_map2
        # Don't change the lock to check that the cache will be kept.
        # Acl.roles_lock = 'changed'

        acl1 = Acl(area='my_area', user='user_1')
        acl2 = Acl(area='my_area', user='user_2')

        self.assertEqual(acl1.has_access('content', 'add'), True)
        self.assertEqual(acl1.has_access('content', 'edit'), True)
        self.assertEqual(acl1.has_access('content', 'delete'), True)

        self.assertEqual(acl2.has_access('content', 'add'), True)
        self.assertEqual(acl2.has_access('content', 'edit'), True)
        self.assertEqual(acl2.has_access('content', 'delete'), False)

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

        self.assertEqual(acl1.has_access('content', 'add'), True)
        self.assertEqual(acl1.has_access('content', 'edit'), True)
        self.assertEqual(acl1.has_access('content', 'delete'), True)

        self.assertEqual(acl2.has_access('content', 'add'), True)
        self.assertEqual(acl2.has_access('content', 'edit'), True)
        self.assertEqual(acl2.has_access('content', 'delete'), False)

        roles_map2 = {
            'editor':      [('content', '*', True),],
            'contributor': [('content', '*', True), ('content', 'delete', False), ('content', 'add', False)],
        }
        Acl.roles_map = roles_map2
        Acl.roles_lock = 'changed'

        acl1 = Acl(area='my_area', user='user_1')
        acl2 = Acl(area='my_area', user='user_2')

        self.assertEqual(acl1.has_access('content', 'add'), True)
        self.assertEqual(acl1.has_access('content', 'edit'), True)
        self.assertEqual(acl1.has_access('content', 'delete'), True)

        self.assertEqual(acl2.has_access('content', 'add'), False)
        self.assertEqual(acl2.has_access('content', 'edit'), True)
        self.assertEqual(acl2.has_access('content', 'delete'), False)

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
        self.assertEqual(handler.acl.has_access('content', 'add'), True)
        self.assertEqual(handler.acl.has_access('content', 'edit'), True)
        self.assertEqual(handler.acl.has_access('content', 'delete'), True)
        self.assertEqual(handler.acl.has_access('foo', 'delete'), False)


if __name__ == '__main__':
    test_utils.main()
