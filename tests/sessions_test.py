import datetime
import functools
import time

from tipfy.sessions import SecureCookieSerializer

import test_utils


class SessionsTest(test_utils.BaseTestCase):
    def test_secure_cookie_serializer(self):
        def get_timestamp(*args):
            d = datetime.datetime(*args)
            return int(time.mktime(d.timetuple()))

        value = ['a', 'b', 'c']
        result = 'WyJhIiwiYiIsImMiXQ==|1293847200|f7f95c30ba7cc2c1d49677e6b0eaf477504ad548'

        serializer = SecureCookieSerializer('secret-key')
        serializer.get_timestamp = functools.partial(get_timestamp, 2011, 1,
                                                     1, 0, 0, 0)
        # ok
        rv = serializer.serialize('foo', value)
        self.assertEqual(rv, result)

        # ok
        rv = serializer.deserialize('foo', result)
        self.assertEqual(rv, value)

        # no value
        rv = serializer.deserialize('foo', None)
        self.assertEqual(rv, None)

        # not 3 parts
        rv = serializer.deserialize('foo', 'a|b')
        self.assertEqual(rv, None)

        # bad signature
        rv = serializer.deserialize('foo', result + 'foo')
        self.assertEqual(rv, None)

        # too old
        serializer.get_timestamp = functools.partial(get_timestamp, 2011, 1,
                                                     3, 0, 0, 0)
        rv = serializer.deserialize('foo', result, max_age=86400)
        self.assertEqual(rv, None)

        # not correctly encoded
        serializer2 = SecureCookieSerializer('foo')
        serializer2.encode = lambda x: 'foo'
        result2 = serializer2.serialize('foo', value)
        rv2 = serializer2.deserialize('foo', result2)
        self.assertEqual(rv2, None)


if __name__ == '__main__':
    test_utils.main()
