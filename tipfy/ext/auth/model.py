# -*- coding: utf-8 -*-
"""
    tipfy.ext.auth.model
    ~~~~~~~~~~~~~~~~~~~~

    Base model for authenticated users.

    This module derives from `Zine`_.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import datetime
import string
from random import choice
from hashlib import sha1, md5

from google.appengine.ext import db

from tipfy import get_config

SALT_CHARS = string.ascii_letters + string.digits


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
    #: Authentication identifier, depending on the auth method used.
    #: own|username
    #: gae|user_id
    #: openid|identifier
    auth_id = db.StringProperty(required=True)
    # Session id, renewed periodically for improved security.
    session_id = db.StringProperty(required=True)
    # Session id last renewal date.
    session_updated = db.DateTimeProperty(auto_now_add=True)
    # Admin flag.
    is_admin = db.BooleanProperty(required=True, default=False)

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
        :return:
            The newly created user or ``None`` if the username already exists.
        """
        kwargs['username'] = username
        kwargs['key_name'] = username
        kwargs['auth_id'] = auth_id
        # Generate an initial session id.
        kwargs['session_id'] = gen_salt(length=32)

        if 'password_hash' in kwargs:
            # Password is already hashed.
            kwargs['password'] = kwargs.pop('password_hash')
        elif 'password' in kwargs:
            # Password is not hashed: generate a hash.
            kwargs['password'] = gen_pwhash(kwargs['password'])

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
        :return:
            ``None``.
        """
        self.password = gen_pwhash(new_password)

    def check_password(self, password):
        """Checks if a password is valid. This is done with form login

        :param password:
            Password to be checked.
        :return:
            ``True`` is the password is valid, ``False`` otherwise.
        """
        if check_password(self.password, password) != True:
            return False

        # Check if session id needs to be renewed.
        self._renew_session()
        return True

    def check_session(self, session_id):
        """Checks if a session id is valid.

        :param session_id:
            Session id to be checked.
        :return:
            ``True`` is the session id is valid, ``False`` otherwise.
        """
        if self.session_id != session_id:
            return False

        # Check if session id needs to be renewed.
        self._renew_session()
        return True

    def _renew_session(self, force=False):
        """Renews the session id if its expiration time has passed.

        :param force:
            ``True`` to force the session id to be renewed, ``False`` to check
            if the expiration time has passed.
        :return:
            ``None``.
        """
        if force is False:
            # Only renew the session id if it is too old.
            expires = datetime.timedelta(seconds=get_config('tipfy.ext.auth',
                'session_id_max_age'))

            force = (self.session_updated + expires < datetime.datetime.now())

        if force is True:
            self.session_id = gen_salt(length=32)
            self.session_updated = datetime.datetime.now()
            self.put()

    def __unicode__(self):
        """Returns this entity's username.

        :return:
            Username, as unicode.
        """
        return unicode(self.username)

    def __str__(self):
        """Returns this entity's username.

        :return:
            Username, as unicode.
        """
        return self.__unicode__()

    def __eq__(self, obj):
        """Compares this user entity with another one.

        :return:
            ``True`` if both entities have same key, ``False`` otherwise.
        """
        if not obj:
            return False

        return str(self.key()) == str(obj.key())

    def __ne__(self, obj):
        """Compares this user entity with another one.

        :return:
            ``True`` if both entities don't have same key, ``False`` otherwise.
        """
        return not self.__eq__(obj)


def gen_salt(length=10):
    """Generates a random string of SALT_CHARS with specified ``length``.

    :param length:
        Length of the salt.
    :return:
        A random salt.
    """
    if length <= 0:
        raise ValueError('requested salt of length <= 0')

    return ''.join(choice(SALT_CHARS) for i in xrange(length))


def gen_pwhash(password):
    """Returns the password encrypted in sha1 format with a random salt.

    :param password:
        Password to e hashed and formatted.
    :return:
        A hashed and formatted password.
    """
    if isinstance(password, unicode):
        password = password.encode('utf-8')

    salt = gen_salt()
    h = sha1()
    h.update(salt)
    h.update(password)
    return 'sha1$%s$%s' % (salt, h.hexdigest())


def check_password(pwhash, password):
    """Checks a password against a given hash value. Since  many systems save
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

    :param pwhash:
        Hash to be checked.
    :param password:
        Password to be checked.
    :return:
        ``True`` if the password is valid, ``False`` otherwise.
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
