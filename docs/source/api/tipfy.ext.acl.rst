.. _api.tipfy.ext.acl:

tipfy.ext.acl
=============
This extension provides a lightweight access control implementation to check
for user permissions to application resources.

See the `extension wiki page <http://www.tipfy.org/wiki/extensions/acl/>`_.

.. module:: tipfy.ext.acl

.. autoclass:: Acl
   :members: roles_map, roles_lock, __init__, reset, is_one, is_any, is_all,
             has_any_access, has_access

.. autoclass:: AclRules
   :members: get_key_name, get_by_area_and_user, insert_or_update,
             get_roles_and_rules, set_cache, delete_cache, put, delete,
             is_rule_set

.. autoclass:: AclMixin
   :members: acl

