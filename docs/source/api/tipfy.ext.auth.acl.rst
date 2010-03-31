.. _api.tipfy.ext.auth.acl:

tipfy.ext.auth.acl
==================
This module provides a lightweight Access Control List implementation to check
user permissions to application resources.

.. module:: tipfy.ext.auth.acl


Overview
--------
This module provides utilities to manage permissions for anything that
requires some level of restriction, like datastore models or handlers.
Access permissions can be grouped in roles for convenience, so that a new
user can be assigned to a role directly instead of having all his
permissions defined manually. Individual access permissions can then
override or extend the role permissions.

.. note::
   Roles are optional, so this module doesn't define a roles model, to keep
   things simple and fast. Role definitions are set directly in the Acl
   class. The strategy to load roles is open to the implementation: for
   best performance, define them statically in a module.


Usage example:

.. code-block:: python

   # Set a dict of roles with an 'admin' role that has full access and
   # assign users to it. Each role maps to a list of rules. Each rule is a
   # tuple (topic, name, flag), where flag is as bool to allow or disallow
   # access. Wildcard '*' can be used to match all topics and/or names.
   Acl.roles_map = {
       'admin': [
           ('*', '*', True),
       ],
   }

   # Assign users 'user_1' and 'user_2' to the 'admin' role.
   AclRules.insert_or_update(area='my_area', user='user_1', roles=['admin'])
   AclRules.insert_or_update(area='my_area', user='user_2', roles=['admin'])

   # Restrict 'user_2' from accessing a specific resource, adding a new
   # rule with flag set to False. Now this user has access to everything
   # except this resource.
   user_acl = AclRules.get_by_area_and_user('my_area', 'user_2')
   user_acl.rules.append(('UserAdmin', '*', False))
   user_acl.put()

   # Check that 'user_2' permissions are correct.
   acl = Acl(area='my_area', user='user_2')
   assert acl.has_access(topic='UserAdmin', name='save') is False
   assert acl.has_access(topic='AnythingElse', name='put') is True


The Acl object should be created once after a user is loaded, so that
it becomes available for the app to do all necessary permissions checkings.


Acl class
---------
.. autoclass:: Acl
   :members: roles_map, roles_lock, __init__, reset, is_one, is_any, is_all, has_any_access, has_access

