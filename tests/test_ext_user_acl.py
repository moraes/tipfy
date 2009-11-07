# -*- coding: utf-8 -*-
from google.appengine.ext import db
from google.appengine.ext.db import BadValueError

from nose.tools import raises
from tipfy.ext.user.acl import Acl, AclRules


def setup_module():
    """Ensures that datastore is empty."""
    entities = AclRules.all().get()
    assert entities is None

def teardown_module():
    """Removes all test records."""
    Acl.roles_map = {}
    entities = AclRules.all().fetch(100)
    if entities:
        # Delete one by one to also clear memcache.
        for entity in entities:
            entity.delete()

def test_set_rules():
    rules = [
        ('topic_1', 'name_1', True),
        ('topic_1', 'name_2', True),
        ('topic_2', 'name_1', False),
    ]

    # Set rules and save the record.
    user_acl = AclRules.insert_or_update(area='test', name='test', rules=rules)

    # Fetch the record again, and compare.
    user_acl = AclBase.get_by_area_and_user('test', 'test')
    assert user_acl.rules == rules

def test_append_rules():
    rules = [
        ('topic_1', 'name_1', True),
        ('topic_1', 'name_2', True),
        ('topic_2', 'name_1', False),
    ]
    extra_rule = ('topic_3', 'name_3', True)

    # Set rules and save the record.
    user_acl = AclRules.insert_or_update(area='test', name='test', rules=rules)

    # Fetch the record again, and compare.
    user_acl = AclBase.get_by_area_and_user('test', 'test')
    user_acl.rules.append(extra_rule)
    user_acl.put()

    rules.append(extra_rule)

    user_acl = AclRules.get_by_area_and_user('test', 'test')
    assert user_acl.rules == rules

@raises(BadValueError)
def test_set_invalid_rules():
    rules = [
        ('topic_1', 'name_1', True),
        ('topic_1', 'name_2', True),
        ('topic_2', 'name_1', 'invalid'),
    ]

    # Set rules and save the record.
    user_acl = AclRules.insert_or_update(area='test', name='test', rules=rules)

@raises(ValueError)
def test_set_invalid_rules_2():
    rules = [
        ('topic_1', 'name_1', True),
        ('topic_1', 'name_2', True),
        ('topic_2', 'name_1'),
    ]

    # Set rules and save the record.
    user_acl = AclRules.insert_or_update(area='test', name='test', rules=rules)

def test_set_empty_rules():
    rules = []
    # Set rules and save the record.
    user_acl = AclRules.insert_or_update(area='test', name='test')

def test_example():
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
    assert acl.has_access(topic='UserAdmin', name='put') is False
    assert acl.has_access(topic='UserAdmin', name='get') is False
    assert acl.has_access(topic='AnythingElse', name='put') is True

