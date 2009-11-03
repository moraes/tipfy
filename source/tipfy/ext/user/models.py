# -*- coding: utf-8 -*-
"""
    tipfy.ext.user.models
    ~~~~~~~~~~~~~~~~~~~~~

    Authentication models.

    This file derives from Zine and Kay projects.

    :copyright: (c) 2009 by the Zine Team, see AUTHORS for more details.
    :Copyright: (c) 2009 Accense Technology, Inc.
                         Takashi Matsuo <tmatsuo@candit.jp>,
                         Ian Lewis <IanMLewis@gmail.com>
                         All rights reserved.
    :license: BSD, see LICENSE for more details.
"""
import string
from random import choice
from hashlib import sha1, md5

from google.appengine.ext import db

from tipfy import app

SALT_CHARS = string.ascii_lowercase + string.digits


def gen_salt(length=6):
    """Generate a random string of SALT_CHARS with specified ``length``."""
    if length <= 0:
        raise ValueError('requested salt of length <= 0')

    return ''.join(choice(SALT_CHARS) for i in xrange(length))


def gen_pwhash(password):
    """Return a the password encrypted in sha format with a random salt."""
    if isinstance(password, unicode):
        password = password.encode('utf-8')

    salt = gen_salt(6)
    h = sha1()
    h.update(salt)
    h.update(password)
    return 'sha$%s$%s' % (salt, h.hexdigest())


def check_pwhash(pwhash, password):
    """Check a password against a given hash value. Since  many systems save
    md5 passwords with no salt and it's technically impossible to convert this
    to a sha hash with a salt we use this to be able to check for legacy plain
    passwords as well as salted sha passwords::

        plain$$default

    md5 passwords without salt::

        md5$$c21f969b5f03d33d43e04f8f136e7682

    md5 passwords with salt::

        md5$123456$7faa731e3365037d264ae6c2e3c7697e

    sha passwords::

        sha$123456$118083bd04c79ab51944a9ef863efcd9c048dd9a

    Note that the integral passwd column in the table is
    only 60 chars long. If you have a very large salt
    or the plaintext password is too long it will be
    truncated.

    >>> check_pwhash('plain$$default', 'default')
    True
    >>> check_pwhash('sha$$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'password')
    True
    >>> check_pwhash('sha$$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'wrong')
    False
    >>> check_pwhash('md5$xyz$bcc27016b4fdceb2bd1b369d5dc46c3f', u'example')
    True
    >>> check_pwhash('sha$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'password')
    False
    >>> check_pwhash('md42$xyz$bcc27016b4fdceb2bd1b369d5dc46c3f', 'example')
    False
    """
    if isinstance(password, unicode):
        password = password.encode('utf-8')

    if pwhash.count('$') < 2:
        return False

    method, salt, hashval = pwhash.split('$', 2)

    if method == 'plain':
        return hashval == password
    elif method == 'md5':
        h = md5()
    elif method == 'sha':
        h = sha1()
    else:
        return False

    h.update(salt)
    h.update(password)
    return h.hexdigest() == hashval


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
        return user_name

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
        return uuid

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
