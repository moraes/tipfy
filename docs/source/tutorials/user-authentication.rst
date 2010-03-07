User Authentication Tutorial
============================

.. _Tipfy: http://code.google.com/p/tipfy/
.. _OAuth: http://oauth.net/
.. _OpenId: http://openid.net/
.. _App Engine's standard users API: http://code.google.com/appengine/docs/python/users/

`Tipfy`_ has an unified user accounts system that supports authentication using:

- Datastore ("own" users)
- `OpenId`_ (Google, Yahoo etc)
- `OAuth`_ (Google, Twitter, FriendFeed etc)
- Facebook
- `App Engine's standard users API`_

You can choose one, all or a mix of the available authentication systems, or
implement new authentication methods to plug into the user system.

Independently of the chosen method, `Tipfy`_ will require the authenticated
user to create an account in the site, so that an `User` entity is saved in the
datastore and becomes available for the application to reference existing users.
`Tipfy`_ provides a default user model in :class:`tipfy.ext.user.model.User`,
but you can configure it to use a custom model if needed.


Authentication with App Engine's users API
------------------------------------------
This is the default authentication method, and also the simplest to
implement: no configuration is required and you only need to create a request
handler for logged in users to save an account. Let's do it.


Authentication with "own" users
-------------------------------
Coming soon!


Authentication with OpenId, OAuth and Facebook
----------------------------------------------
Coming soon!
