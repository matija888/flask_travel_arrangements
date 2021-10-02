import os
import unittest

from flask_testing import TestCase
from flask_login import LoginManager

from app import create_app, db
from app.models import User

# Creates a new instance of the Flask application. The reason for this
# is that we can't interrupt the application instance that is currently
# running and serving requests.
app = create_app('testing')


class TestApp(TestCase):
    def create_app(self):
        self.app = create_app('testing')
        self.app.config['DEBUG'] = True

        self.client = self.app.test_client(self)
        return self.app

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()

        loginmgr = LoginManager(app)
        loginmgr.init_app(app)
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login_page_get(self):
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)

    def test_login_page_post_unrecognized_user(self):
        response = self.client.post('/auth/login', data=dict(username='test_user'))
        self.assertEqual(response.status_code, 302)
        self.assertMessageFlashed(
            'There is no account with the username that you entered. '
            'Please check your username or register a new account.',
            'error'
        )

    def test_register_page_get_method(self):
        response = self.client.get('/auth/register')
        self.assertTemplateUsed('auth/register.html')
        self.assertEqual(response.status_code, 200)

    def test_register_user_with_incorrect_password_retyping(self):
        response = self.client.post('/auth/register', data=dict(
            first_name='Test', last_name='User', username='test_user', email='test@novelic.com', password='testing111',
            confirm_password='testing11'
        ))
        self.assertEqual(response.status_code, 200)
        self.assertMessageFlashed(
            'The password that you entered does not match with confirmed password. Please try again', 'error'
        )

    def test_register_with_already_existing_username(self):
        self.client.post('/auth/register', data=dict(
            first_name='Test', last_name='User', username='test_user', email='test@novelic.com', password='testing111',
            confirm_password='testing111'
        ))
        response = self.client.post('/auth/register', data=dict(
            first_name='Test', last_name='User', username='test_user', email='test@novelic.com', password='testing111',
            confirm_password='testing111'
        ))
        self.assertEqual(response.status_code, 302)
        self.assertMessageFlashed(
            'The username that you have just entered already exists in the database.'
        )

    def test_login_page_post_recognized_user(self):
        # first register user in order to test auth with wrong password
        response = self.client.post('/auth/register', data=dict(
            first_name='Test', last_name='User', username='test_user', email='test@novelic.com', password='testing123',
            confirm_password='testing123'
        ))
        self.assertEqual(response.status_code, 302)

        # WRONG PASSWORD
        response = self.client.post('/auth/login', data=dict(username='test_user', password='testing'))
        self.assertEqual(response.status_code, 302)
        self.assertMessageFlashed('Incorrect username or password!', 'error')

        # CORRECT PASSWORD
        response = self.client.post('/auth/login', data=dict(username='test_user', password='testing123'))
        self.assertEqual(response.status_code, 302)
        self.assertMessageFlashed('You have successfully login. Welcome!')

    def test_logout(self):
        response = self.client.get('auth/logout')
        self.assertEqual(response.status_code, 302)

    def test_models(self):
        users = User.query.all()
        self.assertEqual(len(users), 0)

        user = User(
            first_name='John', last_name='Doe', username='john11', password='pass',
            email='john.doe@example.com', account_type='TOURIST'
        )
        db.session.add(user)
        db.session.commit()

        users = User.query.all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].first_name, 'John')
        self.assertEqual(users[0].last_name, 'Doe')

    def test_try_to_access_not_readable_attribute_password(self):
        user = User(
            first_name='Test', last_name='User', username='test_user', email='test@novelic.com', password='testing111',
            account_type='TOURIST'
        )
        db.session.add(user)
        db.session.commit()
        user = User.query.first()
        with self.assertRaises(AttributeError):
            user.password


if __name__ == '__main__':
    unittest.main()
