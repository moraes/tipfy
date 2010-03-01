# -*- coding: utf-8 -*-
"""
    tipfy.ext.user.models
    ~~~~~~~~~~~~~~~~~~~~~

    Base model for authenticated users.

    This module derives from `Zine`_.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import string
from random import choice
from hashlib import sha1, md5

from google.appengine.ext import db

SALT_CHARS = string.ascii_letters + string.digits


class User(db.Model):
    """Universal user model. Can be used for Google acounts or other
    authentication systems.
    """
    #: Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    #: User defined unique name, also used as key_name.
    username = db.StringProperty(required=True)
    #: Password, only set for own authentication.
    password = db.StringProperty(required=False)
    #: Authentication identifier.
    #: google|google_user.user_id()
    #: openid|
    #: oauth|
    #: own|username
    auth_id = db.StringProperty(required=True)

    email = db.EmailProperty()
    is_admin = db.BooleanProperty(required=True, default=False)

    @classmethod
    def get_key_name(cls, username):
        return username

    @classmethod
    def get_by_username(cls, username):
        return cls.get_by_key_name(cls.get_key_name(username))

    @classmethod
    def get_by_auth_id(cls, auth_id):
        return cls.all().filter('auth_id =', auth_id).get()

    @classmethod
    def create(cls, username, **kwargs):
        """Creates a new user and returns it. If the username already exists,
        returns None.
        """
        key_name = cls.get_key_name(username)

        if 'password_hash' in kwargs:
            kwargs['password'] = kwargs.pop('password_hash')
        elif 'password' in kwargs:
            kwargs['password'] = gen_pwhash(kwargs['password'])

        def txn():
            user = cls.get_by_key_name(key_name)
            if user:
                # Username already exists.
                return None

            user = cls(key_name=key_name, username=username, **kwargs)
            user.put()
            return user

        return db.run_in_transaction(txn)

    def check_password(self, password):
        return check_password(self.password, password)

    def __unicode__(self):
        return unicode(self.username)

    def __str__(self):
        return self.__unicode__()

    def __eq__(self, obj):
        if not obj:
            return False

        return str(self.key()) == str(obj.key())

    def __ne__(self, obj):
        return not self.__eq__(obj)


def gen_salt(length=10):
    """Generate a random string of SALT_CHARS with specified ``length``."""
    if length <= 0:
        raise ValueError('requested salt of length <= 0')

    return ''.join(choice(SALT_CHARS) for i in xrange(length))


def gen_pwhash(password):
    """Return the password encrypted in sha1 format with a random salt."""
    if isinstance(password, unicode):
        password = password.encode('utf-8')

    salt = gen_salt()
    h = sha1()
    h.update(salt)
    h.update(password)
    return 'sha1$%s$%s' % (salt, h.hexdigest())


def check_password(pwhash, password):
    """Check a password against a given hash value. Since  many systems save
    md5 passwords with no salt and it's technically impossible to convert this
    to a sha hash with a salt we use this to be able to check for legacy plain
    or salted md5 passwords as well as salted sha passwords::

        plain$$default

    md5 passwords without salt::

        md5$$c21f969b5f03d33d43e04f8f136e7682

    md5 passwords with salt::

        md5$123456$7faa731e3365037d264ae6c2e3c7697e

    sha passwords::

        sha1$123456$118083bd04c79ab51944a9ef863efcd9c048dd9a

    >>> check_password('plain$$default', 'default')
    True
    >>> check_password('sha1$$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'password')
    True
    >>> check_password('sha1$$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'wrong')
    False
    >>> check_password('md5$xyz$bcc27016b4fdceb2bd1b369d5dc46c3f', u'example')
    True
    >>> check_password('sha1$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'password')
    False
    >>> check_password('md42$xyz$bcc27016b4fdceb2bd1b369d5dc46c3f', 'example')
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
    elif method == 'sha1':
        h = sha1()
    else:
        return False

    h.update(salt)
    h.update(password)
    return h.hexdigest() == hashval
