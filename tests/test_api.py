import unittest
from base64 import b64encode

from flask_testing import TestCase
from flask_login import LoginManager

from app import create_app, db
from app.models import Arrangement, User
from app.auth.views import return_message_to_client


app = create_app('testing')


class TestAPI(TestCase):

    def create_app(self):
        self.app = create_app('testing')
        self.app.config['DEBUG'] = True
        self.app.config['TESTING'] = True

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

    def test_insert_arrangement_bad_request(self):
        # send POST request without any data from the client
        response = self.client.post('/api/v1.0/arrangements', json={})
        self.assertEqual(response.status_code, 400)

        error_msg = 'destination data is required for creating a new arrangement! '
        error_msg += 'Please add them in the the HTTP body and send the request again.'
        msg = {'message': error_msg}
        self.assertEqual(response.json, msg)

        # send some data, but not all
        # -> number_of_persons is the next field that is missing considered by the backend logic
        response = self.client.post(
            '/api/v1.0/arrangements', json={
                'destination': 'Serbia',
                'description': 'Stara planina zimovanje',
                'start_date': '01.12.2021',
                'end_date': '15.12.2021',
            }
        )
        self.assertEqual(response.status_code, 400)
        error_msg = 'number_of_persons data is required for creating a new arrangement! '
        error_msg += 'Please add them in the the HTTP body and send the request again.'
        msg = {'message': error_msg}
        self.assertEqual(response.json, msg)

    def test_insert_arrangement_good_request(self):
        response = self.client.post(
            '/api/v1.0/arrangements', json={
                'destination': 'Serbia',
                'description': 'Stara planina zimovanje',
                'start_date': '01.12.2021',
                'end_date': '15.12.2021',
                'number_of_persons': 2,
                'price': 100.88
            }
        )
        arrangement = Arrangement.get_arrangement_json(arrangement_id=1)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, arrangement)

    def test_insert_9_arrangements(self):
        for month in range(1, 10):
            self.client.post(
                '/api/v1.0/arrangements', json={
                    'destination': 'Test destination',
                    'description': 'Test desc',
                    'start_date': '01.{}.2021'.format(month),
                    'end_date': '15.{}.2021'.format(month),
                    'number_of_persons': 2,
                    'price': 100.88
                }
            )
        arrangements = Arrangement.query.all()
        self.assertEqual(len(arrangements), 9)

    def test_get_arrangements(self):
        self.test_insert_9_arrangements()
        # get all arrangements without passing column order or page
        response = self.client.get('/api/v1.0/arrangements')
        self.assertEqual(response.status_code, 200)

        # without passing page
        response = self.client.get('/api/v1.0/arrangements?columns_order=start_date asc')
        self.assertEqual(len(response.json), 5)

        # get first page with start_date in asc order
        response = self.client.get('/api/v1.0/arrangements?columns_order=start_date asc&page=2')
        self.assertEqual(len(response.json), 4)

        # get first page with start_date in desc order
        response = self.client.get('/api/v1.0/arrangements?columns_order=start_date desc&page=3')
        self.assertEqual(len(response.json), 0)

    def test_login(self):
        user = User(
            first_name='Test', last_name='test', email='test@user.com', username='test_user', password='test',
            desired_account_type='TOURIST'
        )
        db.session.add(user)
        db.session.commit()
        # GET should be not allowed method
        response = self.client.get('/auth/api/v1.0/login')
        self.assertEqual(response.json, {'message': 'Method Not Allowed'})
        self.assertEqual(response.status_code, return_message_to_client('Method Not Allowed', 405)[1])

        # POST request with WRONG USERNAME
        form_data = b64encode(b"wrong_username:123456").decode('utf-8')
        response = self.client.post('/auth/api/v1.0/login', headers={'Authorization': 'Basic {}'.format(form_data)})
        msg = 'There is no account with the username that you entered. '
        msg += 'Please check your username or register a new account.'
        self.assertEqual(response.json, {'message': msg})
        self.assertEqual(response.status_code, return_message_to_client('Method Not Allowed', 401)[1])

        # POST request with WRONG username and password
        form_data = b64encode(b"test_user:123456").decode('utf-8')
        response = self.client.post('/auth/api/v1.0/login', headers={'Authorization': 'Basic {}'.format(form_data)})
        self.assertEqual(response.json, {'message': 'Incorrect username or password!'})
        self.assertEqual(response.status_code, return_message_to_client('Method Not Allowed', 401)[1])

        # POST request with CORRECT username and password
        form_data = b64encode(b"test_user:test").decode('utf-8')
        response = self.client.post('/auth/api/v1.0/login', headers={'Authorization': 'Basic {}'.format(form_data)})
        self.assertEqual(response.json, {'message': 'You have successfully login. Welcome!'})
        self.assertEqual(response.status_code, return_message_to_client('Method Not Allowed', 200)[1])

    def test_register(self):
        self.test_login()
        # GET should be not allowed method
        response = self.client.get('/auth/api/v1.0/register')
        self.assertEqual(response.status_code, 405)

        response = self.client.post(
            '/auth/api/v1.0/register', data=dict(
                first_name='Test', last_name='User 2', email='test@user.com', username='test_user',
                password='test', confirm_password='test', desired_account_type='ADMIN'
            )
        )
        # user ALREADY EXISTS
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json, {'message': 'The username that you have just entered already exists in the database.'}
        )

        # PASSWORD and CONFIRMED password DO NOT MATCH
        response = self.client.post(
            '/auth/api/v1.0/register', data=dict(
                first_name='Test', last_name='User 2', email='test@user.com', username='john',
                password='pass', confirm_password='conf_pass', desired_account_type='ADMIN'
            )
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json,
            {'message': 'The password that you entered does not match with confirmed password. Please try again'}
        )

        # PASSWORD and CONFIRMED password MATCH
        response = self.client.post(
            '/auth/api/v1.0/register', data=dict(
                first_name='Test', last_name='User 2', email='test@user.com', username='john',
                password='pass', confirm_password='pass', desired_account_type='ADMIN'
            )
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json,
            {'message': 'You have successfully created a new user account. Welcome'}
        )


if __name__ == '__main__':
    unittest.main()