# -*- coding: utf-8 -*-
"""
    tipfy.ext.user.acl
    ~~~~~~~~~~~~~~~~~~

    Simple Access Control List.

    This is used to store permissions for anything that requires some
    level of restriction, like datastore models or handlers. Access permissions
    can be grouped in roles for convenience, so that a new user can be assigned
    to a role directly instead of having all his permissions defined manually.
    Individual access permissions can then override or extend the role
    permissions.

    Roles are optional, so this module doesn't define a roles model, to keep
    things simple and fast. Role definitions are set directly in the Acl class.
    The strategy to load roles is open to the implementation: for best
    performance, define them statically in a module.

    Usage example:

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

    # Check that 'user_2' permissions are correct.
    acl = Acl(area='my_area', user='user_2')
    assert acl.has_access(topic='UserAdmin', name='save') is False
    assert acl.has_access(topic='AnythingElse', name='put') is True

    The Acl object should be created once after a user is loaded, so that
    it becomes available for the app to do all necessary permissions checkings.

    Based on concept from Solar's Access and Role classes: http://solarphp.com.

    :copyright: Paul M. Jones <pmjones@solarphp.com>
    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from google.appengine.ext import db
from google.appengine.api import memcache

from tipfy import app
from tipfy.ext.db import PickleProperty

# Cache for loaded rules.
_rules_map = {}


def validate_rules(rules):
    """Ensures that the list of rule tuples is set correctly."""
    assert isinstance(rules, list), 'Rules must be a list'

    for rule in rules:
        assert isinstance(rule, tuple), 'Each rule must be tuple'
        assert len(rule) == 3, 'Each rule must have three elements'
        assert isinstance(rule[0], basestring), 'Rule topic must be a string'
        assert isinstance(rule[1], basestring), 'Rule name must be a string'
        assert isinstance(rule[2], bool), 'Rule flag must be a bool'


class AclRules(db.Model):
    # Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    # Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    # Area to which this role is related.
    area = db.StringProperty(required=True)
    # User identifier.
    user = db.StringProperty(required=True)
    # List of role names.
    roles = db.StringListProperty()
    # Lists of rules. Each rule is a tuple (topic, name, flag).
    rules = PickleProperty(validator=validate_rules)

    @classmethod
    def get_key_name(cls, area, user):
        """Returns this entity's key name, also used as memcache key."""
        return '%s:%s' % (str(area), str(user))

    @classmethod
    def get_by_area_and_user(cls, area, user):
        """Returns a role entity with a given role name in a given area."""
        return cls.get_by_key_name(cls.get_key_name(area, user))

    @classmethod
    def insert_or_update(cls, area, user, roles=None, rules=None):
        key_name = cls.get_key_name(area, user)
        def txn():
            user_acl = cls.get_by_key_name(key_name)
            if user_acl is None:
                user_acl = cls(key_name=key_name, area=area, user=user,
                    rules=[])

            if roles is not None:
                user_acl.roles = roles

            if rules is not None:
                user_acl.rules = rules

            user_acl.put()
            return user_acl

        return db.run_in_transaction(txn)

    @classmethod
    def get_roles_and_rules(cls, area, user, roles_map):
        """Returns a tuple (roles, rules) for a given user in a given area."""
        res = None
        roles_lock = 'undefined'

        cache_key = cls.get_key_name(area, user)
        if cache_key in _rules_map:
            res = _rules_map[cache_key]
        else:
            res = memcache.get(cache_key, namespace=cls.__name__)

        if res is not None:
            roles_lock, roles, rules = res

        if res is None or roles_lock != Acl.roles_lock or app.config.dev:
            entity = cls.get_by_key_name(cache_key)
            if entity is None:
                res = (Acl.roles_lock, [], [])
            else:
                rules = []
                # Apply role rules.
                for role in entity.roles:
                    rules.extend(roles_map.get(role, []))

                # Extend with rules, eventually overriding some role rules.
                rules.extend(entity.rules)

                # Reverse everything, as rules are checked from last to first.
                rules.reverse()

                # Set results for cache, applying current roles_lock.
                res = (Acl.roles_lock, entity.roles, rules)

            cls.set_cache(cache_key, res)

        return (res[1], res[2])

    @classmethod
    def set_cache(cls, cache_key, spec):
        _rules_map[cache_key] = spec
        memcache.set(cache_key, spec, namespace=cls.__name__)

    @classmethod
    def delete_cache(cls, cache_key):
        if cache_key in _rules_map:
            del _rules_map[cache_key]

        memcache.delete(cache_key, namespace=cls.__name__)

    def put(self):
        """Saves the entity and cleans the cache."""
        self.delete_cache(self.get_key_name(self.area, self.user))
        super(AclRules, self).put()

    def delete(self):
        """Deletes the entity and cleans the cache."""
        self.delete_cache(self.get_key_name(self.area, self.user))
        super(AclRules, self).delete()

    def is_rule_set(self, topic, name, flag):
        """Checks if a given rule is set."""
        for rule_topic, rule_name, rule_flag in self.rules:
            if rule_topic == topic and rule_name == name and rule_flag == flag:
                return True

        return False


class Acl(object):
    """Loads access rules and roles for a given user in a given area and
    provides a centralized interface to check permissions."""
    # Dictionary of available role names mapping to list of rules.
    roles_map = {}
    # Lock for role changes. This is needed because if role definitions change
    # we must invalidate existing cache that applied the previous definitions.
    roles_lock = app.config.version_id

    def __init__(self, area, user):
        """Loads access privileges and roles for a given user."""
        if area and user:
            self._roles, self._rules = AclRules.get_roles_and_rules(area, user,
                self.roles_map)
        else:
            self.reset()

    def reset(self):
        """Resets the currently loaded access rules and user roles."""
        self._rules = []
        self._roles = []

    def is_one(self, role):
        """Check to see if a user is in a role."""
        return role in self._roles

    def is_any(self, roles):
        """Check to see if a user is in any of the listed roles."""
        for role in roles:
            if role in self._roles:
                return True

        return False

    def is_all(self, roles):
        """Check to see if a user is in all of the listed roles."""
        for role in roles:
            if role not in self._roles:
                return False

        return True

    def has_any_access(self):
        """Checks if the user has any access or roles."""
        if self._rules or self._roles:
            return True

        return False

    def has_access(self, topic, name):
        """Tells whether or not to allow access to a topic/name combination."""
        if topic == '*' or name == '*':
            raise ValueError("has_access() can't be called passing '*'")

        for rule_topic, rule_name, rule_flag in self._rules:
            if (rule_topic == topic or rule_topic == '*') and \
                (rule_name == name or rule_name == '*'):
                # Topic and name matched, so return the flag.
                return rule_flag

        # No match.
        return False
