# -*- coding: utf-8 -*-
"""
    tipfy.ext.auth.utils
    ~~~~~~~~~~~~~~~~~~~~

    This module implements various cryptographic functions.

    This file derives from Kay and Zine projects.

    :Copyright: (c) 2009 Accense Technology, Inc. All rights reserved.
    :copyright: (c) 2009 by the Zine Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import string
from random import choice
from hashlib import sha1, md5

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
