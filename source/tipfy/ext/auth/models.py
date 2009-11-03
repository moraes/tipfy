# -*- coding: utf-8 -*-
"""
    tipfy.ext.auth
    ~~~~~~~~~~~~~~

    Authentication models.

    This file derives from Kay project.

    :Copyright: (c) 2009 Accense Technology, Inc.
                         Takashi Matsuo <tmatsuo@candit.jp>,
                         Ian Lewis <IanMLewis@gmail.com>
                         All rights reserved.
    :license: BSD, see LICENSE for more details.
"""
from google.appengine.ext import db

from tipfy import app
from tipfy.ext.auth.utils import gen_pwhash, check_pwhash


class User(db.Model):
    """Basic user type that can be used with other login schemes other than
    Google logins
    """
    # Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    # Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    # User defined unique name, also used as key_name.
    user_name = db.StringProperty(required=True)
    email = db.EmailProperty()
    first_name = db.StringProperty(required=False)
    last_name = db.StringProperty(required=False)
    is_admin = db.BooleanProperty(required=True, default=False)

    @classmethod
    def get_key_name(cls, user_name):
        return 'u:%s' % user_name

    @classmethod
    def get_by_user_name(cls, user_name):
        return cls.get_by_key_name(cls.get_key_name(user_name))

    def __unicode__(self):
        return unicode(self.user_name)

    def __str__(self):
        return self.__unicode__()

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def __eq__(self, obj):
        if not obj:
            return False
        return self.key() == obj.key()

    def __ne__(self, obj):
        return not self.__eq__(obj)


class DatastoreUserDBOperationMixin(object):
    def check_password(self, raw_password):
        return check_pwhash(self.password, raw_password)

    def set_password(self, raw_password):
        self.password = gen_pwhash(raw_password)
        return self.put()


class DatastoreUser(User, DatastoreUserDBOperationMixin):
    """A user with own credentials."""
    password = db.StringProperty(required=True)

    def __unicode__(self):
        return unicode(self.user_name)


class GoogleUser(User):
    """An user that uses Google Accounts."""
    # Google user ID.
    user_id = db.IntegerProperty(required=True)

    @classmethod
    def get_by_user(cls, user):
        return cls.all().filter('user_id =', user.user_id()).get()

    def __eq__(self, obj):
        if not obj or obj.is_anonymous():
            return False

        if app.config.dev:
            # It allows us to pose as an user in dev server.
            return self.user_name == obj.user_name
        else:
            return self.key() == obj.key()


class HybridUser(GoogleUser, DatastoreUserDBOperationMixin):
    """GoogleUser/DatastoreUser hybrid model."""
    # Google user ID.
    user_id = db.IntegerProperty(required=False)
    password = db.StringProperty(required=False)


class AnonymousUser(object):
    __slots__ = ('is_admin')
    is_admin = False

    def __unicode__(self):
        return u"AnonymousUser"

    def __str__(self):
        return self.__unicode__()

    def is_anonymous(self):
        return True

    def is_authenticated(self):
        return False

    def key(self):
        return None

    def __eq__(self, obj):
        return False

    def __ne__(self, obj):
        return not self.__eq__(obj)


class TemporarySession(db.Model):
    """Set an unique id as key_name."""
    # Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    # Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    # User entity.
    user = db.ReferenceProperty(required=True)

    @classmethod
    def get_key_name(cls, uuid):
        return 's:%s' % uuid

    @classmethod
    def get_new_session(cls, user):
        from uuid import uuid4

        def txn():
            session = True
            while session is not None:
                uuid = uuid4().hex
                session = cls.get_by_key_name(cls.get_key_name(uuid))

            session = cls(key_name=cls.get_key_name(uuid), user=user)
            session.put()
            return session

        return db.run_in_transaction(txn)

    @property
    def last_login(self):
        return self.updated
