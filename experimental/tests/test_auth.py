import os
import unittest

from gaetestbed import DataStoreTestCase

from tipfy import (Request, RequestHandler, Response, Rule, Tipfy,
    ALLOWED_METHODS)
from tipfy.auth import (AdminRequiredMiddleware, LoginRequiredMiddleware,
    UserRequiredMiddleware, UserRequiredIfAuthenticatedMiddleware,
    admin_required, login_required, user_required,
    user_required_if_authenticated, check_password, create_password_hash,
    create_session_id)
from tipfy.auth.appengine import AppEngineAuthStore
from tipfy.auth.appengine.model import User


class LoginHandler(RequestHandler):
    def get(self, **kwargs):
        return Response('login')


class LogoutHandler(RequestHandler):
    def get(self, **kwargs):
        return Response('logout')


class SignupHandler(RequestHandler):
    def get(self, **kwargs):
        return Response('signup')


class HomeHandler(RequestHandler):
    def get(self, **kwargs):
        return Response('home sweet home')


def get_app():
    app = Tipfy(rules=[
        Rule('/login', name='auth/login', handler=LoginHandler),
        Rule('/logout', name='auth/logout', handler=LogoutHandler),
        Rule('/signup', name='auth/signup', handler=SignupHandler),
    ])
    return app


class TestAppEngineAuthStore(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_user_model(self):
        app = get_app()
        app.router.add(Rule('/', name='home', handler=HomeHandler))

        request = Request.from_values('/')
        app.set_locals(request)

        store = AppEngineAuthStore(app, request)
        self.assertEqual(store.user_model, User)

    def test_login_url(self):
        app = get_app()
        app.router.add(Rule('/', name='home', handler=HomeHandler))

        request = Request.from_values('/')
        app.set_locals(request)
        app.router.match(request)

        store = AppEngineAuthStore(app, request)
        self.assertEqual(store.login_url(), app.url_for('auth/login', redirect='/'))

        dev = app.dev
        app.dev = False
        store.config['secure_urls'] = True

        self.assertEqual(store.login_url(), app.url_for('auth/login', redirect='/', _scheme='https'))

        app.dev = dev
        store.config['secure_urls'] = False

    def test_logout_url(self):
        app = get_app()
        app.router.add(Rule('/', name='home', handler=HomeHandler))

        request = Request.from_values('/')
        app.set_locals(request)
        app.router.match(request)

        store = AppEngineAuthStore(app, request)
        self.assertEqual(store.logout_url(), app.url_for('auth/logout', redirect='/'))

    def test_signup_url(self):
        app = get_app()
        app.router.add(Rule('/', name='home', handler=HomeHandler))

        request = Request.from_values('/')
        app.set_locals(request)
        app.router.match(request)

        store = AppEngineAuthStore(app, request)
        self.assertEqual(store.signup_url(), app.url_for('auth/signup', redirect='/'))


class TestMiddleware(DataStoreTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)

    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

        os.environ.pop('USER_EMAIL', None)
        os.environ.pop('USER_ID', None)
        os.environ.pop('USER_IS_ADMIN', None)

    def test_login_required_middleware_invalid(self):
        class MyHandler(HomeHandler):
            middleware = [LoginRequiredMiddleware()]

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'http://localhost/login?redirect=%2F')

    def test_login_required_decorator_invalid(self):
        class MyHandler(HomeHandler):
            @login_required
            def get(self, **kwargs):
                return Response('home sweet home')

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'http://localhost/login?redirect=%2F')

    def test_login_required_middleware(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        class MyHandler(HomeHandler):
            middleware = [LoginRequiredMiddleware()]

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'home sweet home')

    def test_login_required_decorator(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        class MyHandler(HomeHandler):
            @login_required
            def get(self, **kwargs):
                return Response('home sweet home')

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'home sweet home')

    def test_user_required_middleware_invalid(self):
        class MyHandler(HomeHandler):
            middleware = [UserRequiredMiddleware()]

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'http://localhost/login?redirect=%2F')

    def test_user_required_decorator_invalid(self):
        class MyHandler(HomeHandler):
            @user_required
            def get(self, **kwargs):
                return Response('home sweet home')

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'http://localhost/login?redirect=%2F')

    def test_user_required_middleware_logged_in(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        class MyHandler(HomeHandler):
            middleware = [UserRequiredMiddleware()]

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'http://localhost/signup?redirect=%2F')

    def test_user_required_decorator_logged_in(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        class MyHandler(HomeHandler):
            @user_required
            def get(self, **kwargs):
                return Response('home sweet home')

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'http://localhost/signup?redirect=%2F')

    def test_user_required_middleware_with_user(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        User.create('me', 'gae|me')

        class MyHandler(HomeHandler):
            middleware = [UserRequiredMiddleware()]

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'home sweet home')

    def test_user_required_decorator_with_user(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        User.create('me', 'gae|me')

        class MyHandler(HomeHandler):
            @user_required
            def get(self, **kwargs):
                return Response('home sweet home')

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'home sweet home')

    def test_user_required_if_authenticated_middleware(self):
        class MyHandler(HomeHandler):
            middleware = [UserRequiredIfAuthenticatedMiddleware()]

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'home sweet home')

    def test_user_required_if_authenticate_decorator(self):
        class MyHandler(HomeHandler):
            @user_required_if_authenticated
            def get(self, **kwargs):
                return Response('home sweet home')

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'home sweet home')

    def test_user_required_if_authenticated_middleware_logged_in(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        class MyHandler(HomeHandler):
            middleware = [UserRequiredIfAuthenticatedMiddleware()]

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'http://localhost/signup?redirect=%2F')

    def test_user_required_if_authenticate_decorator_logged_in(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        class MyHandler(HomeHandler):
            @user_required_if_authenticated
            def get(self, **kwargs):
                return Response('home sweet home')

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'http://localhost/signup?redirect=%2F')

    def test_user_required_if_authenticated_middleware_with_user(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        User.create('me', 'gae|me')

        class MyHandler(HomeHandler):
            middleware = [UserRequiredIfAuthenticatedMiddleware()]

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'home sweet home')

    def test_user_required_if_authenticate_decorator_with_user(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        User.create('me', 'gae|me')

        class MyHandler(HomeHandler):
            @user_required_if_authenticated
            def get(self, **kwargs):
                return Response('home sweet home')

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'home sweet home')

    def test_admin_required_middleware(self):
        class MyHandler(HomeHandler):
            middleware = [AdminRequiredMiddleware()]

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'http://localhost/login?redirect=%2F')

    def test_admin_required_decorator(self):
        class MyHandler(HomeHandler):
            @admin_required
            def get(self, **kwargs):
                return Response('home sweet home')

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], 'http://localhost/login?redirect=%2F')

    def test_admin_required_middleware_logged_in(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        class MyHandler(HomeHandler):
            middleware = [AdminRequiredMiddleware()]

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 403)

    def test_admin_required_decorator_logged_in(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        class MyHandler(HomeHandler):
            @admin_required
            def get(self, **kwargs):
                return Response('home sweet home')

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 403)

    def test_admin_required_middleware_with_user(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        User.create('me', 'gae|me')

        class MyHandler(HomeHandler):
            middleware = [AdminRequiredMiddleware()]

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 403)

    def test_admin_required_decorator_withd_user(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        User.create('me', 'gae|me')

        class MyHandler(HomeHandler):
            @admin_required
            def get(self, **kwargs):
                return Response('home sweet home')

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 403)

    def test_admin_required_middleware_with_admin(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        User.create('me', 'gae|me', is_admin=True)

        class MyHandler(HomeHandler):
            middleware = [AdminRequiredMiddleware()]

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'home sweet home')

    def test_admin_required_decorator_with_admin(self):
        os.environ['USER_EMAIL'] = 'me@myself.com'
        os.environ['USER_ID'] = 'me'

        User.create('me', 'gae|me', is_admin=True)

        class MyHandler(HomeHandler):
            @admin_required
            def get(self, **kwargs):
                return Response('home sweet home')

        app = get_app()
        app.router.add(Rule('/', name='home', handler=MyHandler))
        client = app.get_test_client()

        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'home sweet home')


class TestUserModel(DataStoreTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)

    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_create(self):
        user = User.create('my_username', 'my_id')
        self.assertEqual(isinstance(user, User), True)

        # Second one will fail to be created.
        user = User.create('my_username', 'my_id')
        self.assertEqual(user, None)

    def test_create_with_password_hash(self):
        user = User.create('my_username', 'my_id', password_hash='foo')

        self.assertEqual(isinstance(user, User), True)
        self.assertEqual(user.password, 'foo')

    def test_create_with_password(self):
        user = User.create('my_username', 'my_id', password='foo')

        self.assertEqual(isinstance(user, User), True)
        self.assertNotEqual(user.password, 'foo')
        self.assertEqual(len(user.password.split('$')), 3)

    def test_set_password(self):
        user = User.create('my_username', 'my_id', password='foo')
        self.assertEqual(isinstance(user, User), True)

        password = user.password

        user.set_password('bar')
        self.assertNotEqual(user.password, password)

        self.assertNotEqual(user.password, 'bar')
        self.assertEqual(len(user.password.split('$')), 3)

    def test_check_password(self):
        app = Tipfy()
        user = User.create('my_username', 'my_id', password='foo')

        self.assertEqual(user.check_password('foo'), True)
        self.assertEqual(user.check_password('bar'), False)

    def test_check_session(self):
        app = Tipfy()
        user = User.create('my_username', 'my_id', password='foo')

        session_id = user.session_id
        self.assertEqual(user.check_session(session_id), True)
        self.assertEqual(user.check_session('bar'), False)

    def test_get_by_username(self):
        user = User.create('my_username', 'my_id')
        user_1 = User.get_by_username('my_username')

        self.assertEqual(isinstance(user, User), True)
        self.assertEqual(isinstance(user_1, User), True)
        self.assertEqual(str(user.key()), str(user_1.key()))

    def test_get_by_auth_id(self):
        user = User.create('my_username', 'my_id')
        user_1 = User.get_by_auth_id('my_id')

        self.assertEqual(isinstance(user, User), True)
        self.assertEqual(isinstance(user_1, User), True)
        self.assertEqual(str(user.key()), str(user_1.key()))

    def test_unicode(self):
        user_1 = User(username='Calvin', auth_id='test', session_id='test')
        self.assertEqual(unicode(user_1), u'Calvin')

    def test_str(self):
        user_1 = User(username='Hobbes', auth_id='test', session_id='test')
        self.assertEqual(str(user_1), u'Hobbes')

    def test_eq(self):
        user_1 = User(key_name='test', username='Calvin', auth_id='test', session_id='test')
        user_2 = User(key_name='test', username='Calvin', auth_id='test', session_id='test')

        self.assertEqual(user_1, user_2)
        self.assertNotEqual(user_1, '')

    def test_ne(self):
        user_1 = User(key_name='test', username='Calvin', auth_id='test', session_id='test')
        user_2 = User(key_name='test_2', username='Calvin', auth_id='test', session_id='test')

        self.assertEqual((user_1 != user_2), True)

    def test_renew_session(self):
        app = Tipfy()
        user = User.create('my_username', 'my_id')
        user.renew_session()

    def test_renew_session_force(self):
        app = Tipfy()
        user = User.create('my_username', 'my_id')
        user.renew_session(force=True)


class TestMiscelaneous(DataStoreTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)

    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_create_session_id(self):
        self.assertEqual(len(create_session_id()), 32)

    def test_create_password_hash(self):
        res = create_password_hash('foo')
        parts = res.split('$')

        self.assertEqual(parts[0], 'sha1')
        self.assertEqual(len(parts[1]), 32)
        self.assertEqual(len(parts[2]), 40)

        res = create_password_hash(u'bar')
        parts = res.split('$')

        self.assertEqual(parts[0], 'sha1')
        self.assertEqual(len(parts[1]), 32)
        self.assertEqual(len(parts[2]), 40)

    def test_check_password(self):
        self.assertEqual(check_password('plain$$default', 'default'), True)
        self.assertEqual(check_password('sha1$$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'password'), True)
        self.assertEqual(check_password('sha1$$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'wrong'), False)
        self.assertEqual(check_password('md5$xyz$bcc27016b4fdceb2bd1b369d5dc46c3f', u'example'), True)
        self.assertEqual(check_password('sha1$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'password'), False)
        self.assertEqual(check_password('md42$xyz$bcc27016b4fdceb2bd1b369d5dc46c3f', 'example'), False)
