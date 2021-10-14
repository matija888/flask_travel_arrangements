import unittest
from unittest.mock import MagicMock
from base64 import b64encode

from flask import jsonify
from flask_testing import TestCase
from flask_login import LoginManager
from sqlalchemy.exc import IntegrityError

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

    @unittest.mock.patch('flask_login.utils._get_user')
    def test_insert_arrangement_good_request(self, current_user):
        mock_current_user = MagicMock()
        mock_current_user.id = 1
        current_user.return_value = mock_current_user

        self.test_insert_travel_admin()

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

    @unittest.mock.patch('flask_login.utils._get_user')
    def test_insert_9_arrangements(self, current_user):
        mock_current_user = MagicMock()
        mock_current_user.id = 1
        current_user.return_value = mock_current_user

        self.test_insert_travel_guide()
        for month in range(1, 10):
            self.client.post(
                '/api/v1.0/arrangements', json={
                    'destination': 'Test destination',
                    'description': 'Test desc',
                    'start_date': '01.{}.2022'.format(month),
                    'end_date': '15.{}.2022'.format(month),
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

    def test_register_route(self):
        self.test_login()
        # GET should be not allowed method
        response = self.client.get('/auth/api/v1.0/register')
        self.assertEqual(response.status_code, 405)

        response = self.client.post(
            '/auth/api/v1.0/register', json=dict(
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
            '/auth/api/v1.0/register', json=dict(
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
            '/auth/api/v1.0/register', json=dict(
                first_name='Test', last_name='User 2', email='test@user.com', username='john',
                password='pass', confirm_password='pass', desired_account_type='ADMIN'
            )
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json,
            {'message': 'You have successfully created a new user account. Welcome'}
        )

    def test_insert_travel_guide(self):
        response = self.client.post(
            '/auth/api/v1.0/register', json=dict(
                first_name='Travel', last_name='Guide', email='travel@guide.com', username='guide',
                password='guide', confirm_password='guide', desired_account_type='TRAVEL GUIDE'
            )
        )
        self.assertEqual(response.status_code, 201)
        tourist = User.query.filter_by(desired_account_type='TRAVEL GUIDE').first()
        tourist.account_type = 'TRAVEL GUIDE'
        db.session.add(tourist)
        db.session.commit()

    def test_insert_travel_admin(self):
        response = self.client.post(
            '/auth/api/v1.0/register', json=dict(
                first_name='Travel', last_name='admin', email='admin@admin.com', username='admin',
                password='admin', confirm_password='admin', desired_account_type='ADMIN'
            )
        )
        self.assertEqual(response.status_code, 201)
        tourist = User.query.filter_by(desired_account_type='ADMIN').first()
        tourist.account_type = 'ADMIN'
        db.session.add(tourist)
        db.session.commit()

    @unittest.mock.patch('flask_login.utils._get_user')
    def test_update_arrangement(self, current_user):
        mock_current_user = MagicMock()
        mock_current_user.id = 1
        mock_current_user.account_type = 'ADMIN'
        current_user.return_value = mock_current_user

        self.test_insert_travel_admin()
        self.test_insert_9_arrangements()
        # send PUT request without any data
        response = self.client.put('/api/v1.0/arrangements/5')
        self.assertEqual(response.status_code, 400)
        error_msg = 'You need to send json data in order to update arrangement.'
        self.assertEqual(response.json, {'message': error_msg})

        # send PUT request with data (except travel_guide_id)
        updated_destination = 'Destination updated'
        updated_description = 'Description updated'
        updated_start_date = '01.01.2021'
        updated_end_date = '15.01.2021'
        response = self.client.put('/api/v1.0/arrangements/4', json=dict(
            destination=updated_destination, description=updated_description,
            start_date=updated_start_date, end_date=updated_end_date, travel_guide_id=2
        ))
        self.assertEqual(response.status_code, 200)
        arrangement = Arrangement.query.filter_by(id=4).first()
        self.assertEqual(arrangement.destination, updated_destination)
        self.assertEqual(arrangement.description, updated_description)
        self.assertEqual(arrangement.start_date.strftime('%d.%m.%Y'), updated_start_date)
        self.assertEqual(arrangement.end_date.strftime('%d.%m.%Y'), updated_end_date)
        self.assertEqual(arrangement.travel_guide_id, 2)

        # try to update arrangement with start date in the next 5 days
        response = self.client.put('/api/v1.0/arrangements/4', json=dict(
            destination=updated_destination, description=updated_description,
            start_date=updated_start_date, end_date=updated_end_date
        ))
        msg = 'It is too late to edit arrangement id=4 because start date of the arrangement is 01.01.2021.'
        self.assert404(response, message=msg)

        # change creator of the arrangement with id=5
        arrangement = Arrangement.query.filter_by(id=5).first()
        arrangement.created_by = 2
        db.session.add(arrangement)
        db.session.commit()
        # try to change arrangement which is created by another user
        response = self.client.put('/api/v1.0/arrangements/5', json=dict(
            destination=updated_destination, description=updated_description,
            start_date=updated_start_date, end_date=updated_end_date
        ))
        msg = 'Only creator of the arrangement id 5 can update it!'
        self.assert404(response, message=msg)

    @unittest.mock.patch('flask_login.utils._get_user')
    def test_update_arrangement_with_unavailable_guide(self, current_user):
        mock_current_user = MagicMock()
        mock_current_user.id = 1
        mock_current_user.account_type = 'ADMIN'
        current_user.return_value = mock_current_user

        # insert two arrangements which overlapped
        self.test_insert_9_arrangements()

        # assign guide to arrangement=1 (01.01.2022 - 15.01.2022)
        response = self.client.put('/api/v1.0/arrangements/1', json=dict(
            travel_guide_id=1
        ))
        self.assert200(response)

        arrangement = Arrangement.query.filter_by(id=2).first()
        arrangement.start_date = '10.01.2022'
        arrangement.end_date = '25.01.2022'
        db.session.add(arrangement)
        db.session.commit()

        # TRY to assign guide to arrangement=2 (01.01.2022 - 15.01.2022)
        response = self.client.put('/api/v1.0/arrangements/2', json=dict(
            travel_guide_id=1
        ))
        self.assert400(response)

    @unittest.mock.patch('flask_login.utils._get_user')
    def test_update_arrangement_by_travel_guide(self, current_user):
        mock_current_user = MagicMock()
        mock_current_user.id = 1
        mock_current_user.account_type = 'TRAVEL GUIDE'
        current_user.return_value = mock_current_user

        # insert two arrangements which overlapped
        self.test_insert_9_arrangements()
        # assign guide to arrangement=1 (01.01.2022 - 15.01.2022)
        response = self.client.put('/api/v1.0/arrangements/1', json=dict(
            travel_guide_id=1
        ))
        msg = 'You do not have permission to edit this arrangement.'
        msg += 'You can only edit arrangement where you are assigned to be a travel guide.'
        self.assert400(response, message=msg)

        arrangement = Arrangement.query.filter_by(id=1).first()
        arrangement.travel_guide_id = 1
        db.session.add(arrangement)
        db.session.commit()
        # try to edit description which by TRAVEL GUIDE
        response = self.client.put('/api/v1.0/arrangements/1', json=dict(
            start_date='description test'
        ))
        msg = 'You only have permission to edit description of this arrangement.'
        self.assert400(response)
        self.assertEqual(response.json, {'message': msg})

    @unittest.mock.patch('flask_login.utils._get_user')
    def test_update_someone_else_arrangement(self, current_user):
        mock_current_user = MagicMock()
        mock_current_user.id = 1
        mock_current_user.account_type = 'ADMIN'
        current_user.return_value = mock_current_user

        self.test_insert_9_arrangements()

        # send PUT request with data (INCLUDING travel_guide_id)
        with self.assertRaises(IntegrityError):
            response = self.client.put('/api/v1.0/arrangements/5', json=dict(
                destination='', description='',
                start_date='01.05.2022', end_date='10.05.2022', travel_guide_id=3
            ))
            msg = 'You are trying to assign travel_guide who does not exist in the database.'
            self.assert400(response, message=msg)

    def test_update_non_existing_arrangement(self):
        response = self.client.put('/api/v1.0/arrangements/123456', json=dict(
            destination='Test', description='Test',
            start_date='01.01.2022', end_date='10.01.2022'
        ))
        msg = 'Arrangement that you are trying to update does not exist!'
        self.assert404(response, message=msg)

    def test_cancel_arrangement(self):
        # POST is NOT ALLOWED method
        response = self.client.post('/api/v1.0/cancel_arrangement/1')
        self.assert405(response)
        self.assertEqual(response.json, {'message': 'Method Not Allowed!'})

        # try to cancel non existing arrangement
        response = self.client.put('/api/v1.0/cancel_arrangement/1')
        self.assert404(response)

        self.test_insert_arrangement_good_request()

        # PUT is ALLOWED method
        response = self.client.put('/api/v1.0/cancel_arrangement/1')
        self.assert200(response)

    def test_reservations(self):
        self.client.get('/reservations')

    def test_get_all_users(self):
        self.test_insert_travel_guide()
        self.test_insert_travel_admin()
        response = self.client.get('/api/v1.0/users')
        self.assert200(response)
        self.assertEqual(len(response.json), 2)

    @unittest.mock.patch('flask_login.utils._get_user')
    def test_get_my_data(self, current_user):
        mock_current_user = MagicMock()
        mock_current_user.id = 2
        mock_current_user.account_type = 'TRAVEL GUIDE'
        current_user.return_value = mock_current_user

        self.test_insert_travel_guide()
        self.test_insert_travel_admin()

        # send GET request
        response = self.client.get('/api/v1.0/my_data')
        self.assert200(response)
        user = User.get_user_by_id(2)
        self.assertEqual(response.json, user)

    @unittest.mock.patch('flask_login.utils._get_user')
    def test_update_user(self, current_user):
        mock_current_user = MagicMock()
        mock_current_user.id = 2
        mock_current_user.account_type = 'TRAVEL GUIDE'
        current_user.return_value = mock_current_user

        self.test_insert_travel_guide()
        self.test_insert_travel_admin()

        # send PUT request without any data
        response = self.client.put('/api/v1.0/my_data')
        msg = "Request that you send does not have any data. Please send json with new value of your data as a user."
        self.assert400(response, msg)

        # send correct PUT request
        response = self.client.put('/api/v1.0/my_data', json=dict(
            username='updated_username', desired_account_type='ADMIN'
        ))
        self.assert200(response)
        msg = 'You have successfully changed your data.'
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'message': msg})
        user = User.query.filter_by(id=2).first()
        self.assertEqual(user.username, 'updated_username')

        # send a request with wrong desired_account_type
        response = self.client.put('/api/v1.0/my_data', json=dict(desired_account_type='ADMINISTRATOR'))
        msg = 'Please chose one of the following desired_account_type: ADMIN, TOURIST, TRAVEL GUIDE.'
        self.assert400(response, msg)

        # TRAVEL GUIDE send a request for changing account_type to TOURIST (which is not allowed)
        # they can only be changed to ADMIN
        response = self.client.put('/api/v1.0/my_data', json=dict(desired_account_type='TOURIST'))
        msg = 'TRAVEL GUIDE cannot send request for changing their account type to TOURIST.'
        self.assert400(response, msg)

    @unittest.mock.patch('flask_login.utils._get_user')
    def test_account_type_requests(self, current_user):
        mock_current_user = MagicMock()
        mock_current_user.id = 2
        mock_current_user.account_type = 'ADMIN'
        current_user.return_value = mock_current_user

        self.test_insert_travel_guide()
        self.test_insert_travel_admin()
        response = self.client.get('/api/v1.0/account_type_requests')
        pending_account_type_change_requests = []
        self.assert200(response, {'message': jsonify(pending_account_type_change_requests)})

        mock_current_user.id = 1
        mock_current_user.account_type = 'TRAVEL GUIDE'
        current_user.return_value = mock_current_user
        self.client.put('/api/v1.0/my_data', json=dict(desired_account_type='ADMIN'))

        # after changing desired account type to ADMIN we need to get one request
        response = self.client.get('/api/v1.0/account_type_requests')
        user = User.get_user_by_id(1)
        self.assertEqual(user['id'], 1)
        self.assertEqual(user['account_type'], 'TRAVEL GUIDE')
        self.assertEqual(user['desired_account_type'], 'ADMIN')
        self.assert200(response, {'message': jsonify(pending_account_type_change_requests)})

    @unittest.mock.patch('flask_login.utils._get_user')
    def test_resolve_account_type_requests(self, current_user):
        self.test_account_type_requests()
        mock_current_user = MagicMock()
        mock_current_user.account_type = 'ADMIN'
        current_user.return_value = mock_current_user

        # 'approve' is not valid action. It must be 'approved'
        response = self.client.put('/api/v1.0/account_type_requests/1/approve')
        msg = 'You need to use /<user_id>/approved or <user_id>/rejected as arguments in order to resolve the request.'
        self.assert400(response, msg)

        response = self.client.put('/api/v1.0/account_type_requests/1/approved')
        msg = 'You have just approved request from Travel Guide '
        msg += ' to give them ADMIN permissions.'
        self.assert200(response, msg)

        # try to reject request just after approve it. It is not allowed
        response = self.client.put('/api/v1.0/account_type_requests/1/rejected')
        msg = 'This user did not send request or their request has been already resolved.'
        self.assert400(response, msg)

        # revert back user.confirmed_desired_account_type to pending and then reject
        user = User.query.filter_by(id=1).first()
        user.confirmed_desired_account_type = 'pending'
        user.account_type = 'TRAVEL GUIDE'
        db.session.add(user)
        db.session.commit()
        response = self.client.put('/api/v1.0/account_type_requests/1/rejected')
        msg = 'You have just rejected request from Travel Guide '
        msg += f'to give them ADMIN permissions.'
        self.assert200(response, msg)

    def test_anonymous_arrangements_page(self):
        response = self.client.get('/api/v1.0/arrangements')
        arrangements = Arrangement.get_basic_arrangements_info()
        self.assert200(response, {'message': arrangements})

    @unittest.mock.patch('flask_login.utils._get_user')
    def test_wrong_sort_args_for_sorting_arrangements(self, current_user):
        mock_current_user = MagicMock()
        mock_current_user.account_type = 'ADMIN'
        mock_current_user.is_anonymous = False
        current_user.return_value = mock_current_user

        response = self.client.get('/api/v1.0/arrangements?columns_order=wrong_sort_argument')
        msg = 'If you want to sort arrangements please use ?columns_order=column_name asc/desc'
        self.assert400(response, msg)

    def test_search_arrangements_by_date(self):
        self.test_insert_9_arrangements()
        response = self.client.get('/api/v1.0/search_arrangements?start_date=01.01.2022&end_date=01.05.2022')
        self.assertEqual(len(response.json), 5)

    @unittest.mock.patch('flask_login.utils._get_user')
    def test_insert_reservation(self, current_user):
        mock_current_user = MagicMock()
        mock_current_user.account_type = 'ADMIN'
        current_user.return_value = mock_current_user

        # first insert 9 arrangements as ADMIN
        self.test_insert_9_arrangements()

        # change account_type to TOURIST who is allowed to insert reservation
        self.app.config['LOGIN_DISABLED'] = False  # we do this in order to test TOURIST route for creating reservation
        mock_current_user.account_type = 'TOURIST'
        mock_current_user.id = 1
        current_user.return_value = mock_current_user
        response = self.client.post('/api/v1.0/reservations', json=dict(
            arrangement_id=1, number_of_persons=1
        ))
        self.assertEqual(response.status_code, 201)
        msg = 'You have successfully created reservation id 1'
        self.assertEqual(response.json['message'], msg)

        # change arrangement which is too late for reservation
        arrangement = Arrangement.query.filter_by(id=5).first()
        arrangement.start_date = '18.10.2021'
        arrangement.end_date = '28.10.2021'
        db.session.add(arrangement)
        db.session.commit()
        response = self.client.post('/api/v1.0/reservations', json=dict(
            arrangement_id=5, number_of_persons=1
        ))
        self.assert400(response)
        msg = "It is too late to create reservation for this arrangement since it starts on 18.10.2021"
        self.assertEqual(response.json['message'], msg)

        # send reservation for more persons than it is defined in arrangement
        arrangement = Arrangement.query.filter_by(id=5).first()
        arrangement.start_date = '30.11.2021'
        arrangement.end_date = '15.12.2021'
        db.session.add(arrangement)
        db.session.commit()
        response = self.client.post('/api/v1.0/reservations', json=dict(
            arrangement_id=5, number_of_persons=5
        ))
        self.assert400(response)
        msg = 'You cannot book reservation with number of persons greater than '
        msg += 'remaining 2 unbooked reservation(places).'
        self.assertEqual(response.json['message'], msg)

        # send reservation to the same arrangement_id=5 with number of persons more than available(1 place)
        self.test_register_route()
        mock_current_user.id = 2
        current_user.return_value = mock_current_user
        response = self.client.post('/api/v1.0/reservations', json=dict(
            arrangement_id=1, number_of_persons=2
        ))
        msg = 'You cannot reserve more than currently available places for this arrangement.'
        self.assert400(response)
        self.assertEqual(response.json['message'], msg)

    def test_cancel_arrangement(self):
        response = self.client.put('/api/v1.0/cancel_arrangement/1')
        self.assert404(response)

        self.test_insert_9_arrangements()
        response = self.client.put('/api/v1.0/cancel_arrangement/1')
        self.assert200(response)
        msg = 'You have successfully canceled arrangement id 1'
        self.assertEqual(response.json['message'], msg)

        # put reservation for arrangement=1 which starts in January 2022


if __name__ == '__main__':
    unittest.main()