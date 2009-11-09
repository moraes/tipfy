# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.user.acl
"""
import unittest
from _setup import get_app

class TestAcl(unittest.TestCase):
    def setUp(self):
        get_app()

        from tipfy.ext.user.acl import Acl, AclRules
        self.Acl = Acl
        self.Acl.roles_map = {}
        self.AclRules = AclRules

    def test_set_rules(self):
        """Test setting and appending rules."""
        rules = [
            ('topic_1', 'name_1', True),
            ('topic_1', 'name_2', True),
            ('topic_2', 'name_1', False),
        ]
        extra_rule = ('topic_3', 'name_3', True)

        # Set emnpty rules.
        user_acl = self.AclRules.insert_or_update(area='test', user='test')

        # Set rules and save the record.
        user_acl = self.AclRules.insert_or_update(area='test', user='test', rules=rules)

        # Fetch the record again, and compare.
        user_acl = self.AclRules.get_by_area_and_user('test', 'test')
        self.assertEqual(user_acl.rules, rules)

        # Append more rules.
        user_acl.rules.append(extra_rule)
        user_acl.put()
        rules.append(extra_rule)

        # Fetch the record again, and compare.
        user_acl = self.AclRules.get_by_area_and_user('test', 'test')
        self.assertEqual(user_acl.rules, rules)

    def test_set_invalid_rules(self):
        rules = {}
        self.assertRaises(AssertionError, self.AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = ['foo', 'bar', True]
        self.assertRaises(AssertionError, self.AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = [('foo',)]
        self.assertRaises(AssertionError, self.AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = [('foo', 'bar')]
        self.assertRaises(AssertionError, self.AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = [(1, 2, 3)]
        self.assertRaises(AssertionError, self.AclRules.insert_or_update, area='test', user='test', rules=rules)

        rules = [('foo', 'bar', True)]
        self.AclRules.insert_or_update(area='test', user='test', rules=rules)
        user_acl = self.AclRules.get_by_area_and_user('test', 'test')
        user_acl.rules.append((1, 2, 3))
        self.assertRaises(AssertionError, user_acl.put)

    def test_example(self):
        """Tests the example set in the acl module."""
        # Set a dict of roles with an 'admin' role that has full access and assign
        # users to it. Each role maps to a list of rules. Each rule is a tuple
        # (topic, name, flag), where flag is as bool to allow or disallow access.
        # Wildcard '*' can be used to match all topics and/or names.
        self.Acl.roles_map = {
            'admin': [
                ('*', '*', True),
            ],
        }

        # Assign users 'user_1' and 'user_2' to the 'admin' role.
        self.AclRules.insert_or_update(area='my_area', user='user_1', roles=['admin'])
        self.AclRules.insert_or_update(area='my_area', user='user_2', roles=['admin'])

        # Restrict 'user_2' from accessing a specific resource, adding a new rule
        # with flag set to False. Now this user has access to everything except this
        # resource.
        user_acl = self.AclRules.get_by_area_and_user('my_area', 'user_2')
        user_acl.rules.append(('UserAdmin', '*', False))
        user_acl.put()

        # Check 'user_2' permission.
        acl = self.Acl(area='my_area', user='user_2')
        self.assertEqual(acl.has_access(topic='UserAdmin', name='save'), False)
        self.assertEqual(acl.has_access(topic='UserAdmin', name='get'), False)
        self.assertEqual(acl.has_access(topic='AnythingElse', name='put'), True)

    def test_is_one(self):
        self.AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor', 'designer'])

        acl = self.Acl(area='my_area', user='user_1')
        self.assertEqual(acl.is_one('editor'), True)
        self.assertEqual(acl.is_one('designer'), True)
        self.assertEqual(acl.is_one('admin'), False)

    def test_is_any(self):
        self.AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor', 'designer'])

        acl = self.Acl(area='my_area', user='user_1')
        self.assertEqual(acl.is_any(['editor', 'admin']), True)
        self.assertEqual(acl.is_any(['admin', 'designer']), True)
        self.assertEqual(acl.is_any(['admin', 'user']), False)

    def test_is_all(self):
        self.AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor', 'designer'])

        acl = self.Acl(area='my_area', user='user_1')
        self.assertEqual(acl.is_all(['editor', 'admin']), False)
        self.assertEqual(acl.is_all(['admin', 'designer']), False)
        self.assertEqual(acl.is_all(['admin', 'user']), False)
        self.assertEqual(acl.is_all(['editor', 'designer']), True)

    def test_has_any_access(self):
        self.AclRules.insert_or_update(area='my_area', user='user_1', roles=['editor', 'designer'])
        self.AclRules.insert_or_update(area='my_area', user='user_2', rules=[('*', '*', True)])
        self.AclRules.insert_or_update(area='my_area', user='user_3')

        acl = self.Acl(area='my_area', user='user_1')
        self.assertEqual(acl.has_any_access(), True)

        acl = self.Acl(area='my_area', user='user_2')
        self.assertEqual(acl.has_any_access(), True)

        acl = self.Acl(area='my_area', user='user_3')
        self.assertEqual(acl.has_any_access(), False)

    def test_has_access(self):
        self.AclRules.insert_or_update(area='my_area', user='user_1', rules=[('*', '*', True)])
        self.AclRules.insert_or_update(area='my_area', user='user_2', rules=[('content', '*', True), ('content', 'delete', False)])
        self.AclRules.insert_or_update(area='my_area', user='user_3', rules=[('content', 'read', True)])

        acl1 = self.Acl(area='my_area', user='user_1')
        acl2 = self.Acl(area='my_area', user='user_2')
        acl3 = self.Acl(area='my_area', user='user_3')

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
        self.Acl.roles_map = {
            'admin':       [('*', '*', True),],
            'editor':      [('content', '*', True),],
            'contributor': [('content', '*', True), ('content', 'delete', False)],
            'designer':    [('design', '*', True),],
        }

        self.AclRules.insert_or_update(area='my_area', user='user_1', roles=['admin'])
        self.AclRules.insert_or_update(area='my_area', user='user_2', roles=['admin'], rules=[('ManageUsers', '*', False)])
        self.AclRules.insert_or_update(area='my_area', user='user_3', roles=['editor'])
        self.AclRules.insert_or_update(area='my_area', user='user_4', roles=['contributor'], rules=[('design', '*', True),])


        acl1 = self.Acl(area='my_area', user='user_1')
        acl2 = self.Acl(area='my_area', user='user_2')
        acl3 = self.Acl(area='my_area', user='user_3')
        acl4 = self.Acl(area='my_area', user='user_4')

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
