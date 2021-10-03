import os
import unittest
from datetime import date

from flask_testing import TestCase
from flask_login import LoginManager

from app import create_app, db
from app.models import User, Arrangement

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

    def test_register_user(self):
        self.client.post('/auth/register', data=dict(
            first_name='Test', last_name='User', username='test_user', email='test@novelic.com', password='testing111',
            confirm_password='testing111', desired_account_type='ADMIN'
        ))

    def test_register_user_with_incorrect_password_retyping(self):
        response = self.client.post('/auth/register', data=dict(
            first_name='Test', last_name='User', username='test_user', email='test@novelic.com', password='testing111',
            confirm_password='testing11', desired_account_type='ADMIN'
        ))
        self.assertEqual(response.status_code, 200)
        self.assertMessageFlashed(
            'The password that you entered does not match with confirmed password. Please try again', 'error'
        )

    def test_register_with_already_existing_username(self):
        self.test_register_user()
        response = self.client.post('/auth/register', data=dict(
            first_name='Test', last_name='User', username='test_user', email='test@novelic.com', password='testing111',
            confirm_password='testing111', desired_account_type='TRAVEL GUIDE'
        ))
        self.assertEqual(response.status_code, 302)
        self.assertMessageFlashed(
            'The username that you have just entered already exists in the database.'
        )

    def test_login_page_post_recognized_user(self):
        # first register user in order to test auth with wrong password
        response = self.client.post('/auth/register', data=dict(
            first_name='Test', last_name='User', username='test_user', email='test@novelic.com', password='testing111',
            confirm_password='testing111', desired_account_type='ADMIN'
        ))
        self.assertEqual(response.status_code, 302)

        # WRONG PASSWORD
        response = self.client.post('/auth/login', data=dict(username='test_user', password='testing'))
        self.assertEqual(response.status_code, 302)
        self.assertMessageFlashed('Incorrect username or password!', 'error')

        # CORRECT PASSWORD
        response = self.client.post('/auth/login', data=dict(username='test_user', password='testing111'))
        self.assertMessageFlashed('You have successfully login. Welcome!')

    def test_logout(self):
        response = self.client.get('auth/logout')
        self.assertEqual(response.status_code, 302)

    def test_models(self):
        users = User.query.all()
        self.assertEqual(len(users), 0)

        user = User(
            first_name='John', last_name='Doe', username='john11', password='pass',
            email='john.doe@example.com', desired_account_type='TOURIST'
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
            account_type='TOURIST', desired_account_type='ADMIN'
        )
        db.session.add(user)
        db.session.commit()
        user = User.query.first()
        with self.assertRaises(AttributeError):
            user.password

    def test_approve_account_type_permission_request(self):
        self.test_register_user()
        response = self.client.get('/manage_account_type_permission_request/1/approve')
        self.assertEqual(response.status_code, 200)
        self.assertMessageFlashed(
            'You have just approved request from Test User to give them ADMIN permissions.'
        )

    def test_reject_account_type_permission_request(self):
        self.test_register_user()
        response = self.client.get('/manage_account_type_permission_request/1/reject')
        self.assertEqual(response.status_code, 200)
        self.assertMessageFlashed(
            'You have just rejected request from Test User to give them ADMIN permissions.'
        )

    def test_admin_login(self):
        self.test_approve_account_type_permission_request()
        self.test_login_page_post_recognized_user()

    def test_loading_user_edit_page(self):
        response = self.client.get('/edit_user_data/1')
        self.assertEqual(response.status_code, 200)

    def test_edit_user_data_post_request(self):
        self.test_register_user()
        response = self.client.post('/edit_user_data/1', data=dict(
            first_name='John', last_name='Doe', username='john_doe', email='john@doe.com',
            desired_account_type='TOURIST'
        ))
        self.assertEqual(response.status_code, 200)
        # check to see if data has been changed
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.username, 'john_doe')
        self.assertEqual(user.email, 'john@doe.com')
        self.assertEqual(user.desired_account_type, 'TOURIST')

    def test_admin_panel_get_request(self):
        response = self.client.get('/admin_panel')
        self.assertEqual(response.status_code, 200)

    def test_travel_arrangements(self):
        response = self.client.get('/arrangements')
        self.assertEqual(response.status_code, 200)

    def test_insert_new_travel_arrangements(self):
        response = self.client.post('/arrangements', data=dict(
            destination='Spain', start_date='2021-11-01', end_date='2021-11-10', description='Autumn in Spain.',
            number_of_persons=2, price=580.00
        ))
        self.assertEqual(response.status_code, 200)
        arrangement = Arrangement.query.filter_by(description='Autumn in Spain.').first()
        self.assertEqual(arrangement.id, 1)
        self.assertEqual(arrangement.start_date, date(2021, 11, 1))
        self.assertEqual(arrangement.end_date, date(2021, 11, 10))
        self.assertEqual(arrangement.number_of_persons, 2)
        self.assertEqual(arrangement.price, 580.00)


if __name__ == '__main__':
    unittest.main()
