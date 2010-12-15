# -*- coding: utf-8 -*-
"""
    tipfy.appengine.auth.model
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Base model for authenticated users.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from __future__ import absolute_import

import datetime

from google.appengine.ext import db

from werkzeug import check_password_hash, generate_password_hash

from tipfy.auth import create_session_id


class User(db.Model):
    """Universal user model. Can be used with App Engine's default users API,
    own auth or third party authentication methods (OpenId, OAuth etc).
    """
    #: Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    #: User defined unique name, also used as key_name.
    username = db.StringProperty(required=True)
    #: Password, only set for own authentication.
    password = db.StringProperty(required=False)
    #: User email
    email = db.EmailProperty()
    # Admin flag.
    is_admin = db.BooleanProperty(required=True, default=False)
    #: Authentication identifier according to the auth method in use. Examples:
    #: * own|username
    #: * gae|user_id
    #: * openid|identifier
    #: * twitter|username
    #: * facebook|username
    auth_id = db.StringProperty(required=True)
    # Flag to persist the auth accross sessions for thirdy party auth.
    auth_remember = db.BooleanProperty(default=False)
    # Auth token, renewed periodically for improved security.
    session_id = db.StringProperty(required=True)
    # Auth token last renewal date.
    session_updated = db.DateTimeProperty(auto_now_add=True)

    @classmethod
    def get_by_username(cls, username):
        return cls.get_by_key_name(username)

    @classmethod
    def get_by_auth_id(cls, auth_id):
        return cls.all().filter('auth_id =', auth_id).get()

    @classmethod
    def create(cls, username, auth_id, **kwargs):
        """Creates a new user and returns it. If the username already exists,
        returns None.

        :param username:
            Unique username.
        :param auth_id:
            Authentication id, according the the authentication method used.
        :param kwargs:
            Additional entity attributes.
        :returns:
            The newly created user or None if the username already exists.
        """
        kwargs['username'] = username
        kwargs['key_name'] = username
        kwargs['auth_id'] = auth_id
        # Generate an initial session id.
        kwargs['session_id'] = create_session_id()

        if 'password_hash' in kwargs:
            # Password is already hashed.
            kwargs['password'] = kwargs.pop('password_hash')
        elif 'password' in kwargs:
            # Password is not hashed: generate a hash.
            kwargs['password'] = generate_password_hash(kwargs['password'])

        def txn():
            if cls.get_by_username(username) is not None:
                # Username already exists.
                return None

            user = cls(**kwargs)
            user.put()
            return user

        return db.run_in_transaction(txn)

    def set_password(self, new_password):
        """Sets a new, plain password.

        :param new_password:
            A plain, not yet hashed password.
        :returns:
            None.
        """
        self.password = generate_password_hash(new_password)

    def check_password(self, password):
        """Checks if a password is valid. This is done with form login

        :param password:
            Password to be checked.
        :returns:
            True is the password is valid, False otherwise.
        """
        if check_password_hash(self.password, password):
            return True

        return False

    def check_session(self, session_id):
        """Checks if an auth token is valid.

        :param session_id:
            Token to be checked.
        :returns:
            True is the token id is valid, False otherwise.
        """
        if self.session_id == session_id:
            return True

        return False

    def renew_session(self, force=False, max_age=None):
        """Renews the session id if its expiration time has passed.

        :param force:
            True to force the session id to be renewed, False to check
            if the expiration time has passed.
        :returns:
            None.
        """
        if not force:
            # Only renew the session id if it is too old.
            expires = datetime.timedelta(seconds=max_age)
            force = (self.session_updated + expires < datetime.datetime.now())

        if force:
            self.session_id = create_session_id()
            self.session_updated = datetime.datetime.now()
            self.put()

    def __unicode__(self):
        """Returns this entity's username.

        :returns:
            Username, as unicode.
        """
        return unicode(self.username)

    def __str__(self):
        """Returns this entity's username.

        :returns:
            Username, as unicode.
        """
        return self.__unicode__()

    def __eq__(self, obj):
        """Compares this user entity with another one.

        :returns:
            True if both entities have same key, False otherwise.
        """
        if not obj:
            return False

        return str(self.key()) == str(obj.key())

    def __ne__(self, obj):
        """Compares this user entity with another one.

        :returns:
            True if both entities don't have same key, False otherwise.
        """
        return not self.__eq__(obj)
