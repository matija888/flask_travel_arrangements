import os
import unittest
from unittest.mock import MagicMock
from datetime import date

from flask_testing import TestCase
from flask_login import LoginManager

from app import create_app, db
from app.models import User, Arrangement, Reservation

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

    def test_register_admin(self):
        self.client.post('/auth/register', data=dict(
            first_name='Test', last_name='User', username='test_user', email='test@novelic.com', password='testing111',
            confirm_password='testing111', desired_account_type='ADMIN'
        ))

    def test_register_travel_guide(self):
        self.client.post('/auth/register', data=dict(
            first_name='Test', last_name='User', username='test_user', email='test@novelic.com', password='testing111',
            confirm_password='testing111', desired_account_type='TRAVEL GUIDE'
        ))

    def test_register_two_travel_guides(self):
        self.client.post('/auth/register', data=dict(
            first_name='Travel', last_name='Guide 1', username='travel_guide_1',
            email='test@novelic.com', password='testing111',
            confirm_password='testing111', desired_account_type='TRAVEL GUIDE'
        ))
        self.client.post('/auth/register', data=dict(
            first_name='Travel', last_name='Guide 2', username='travel_guide_2',
            email='test@novelic.com', password='testing111',
            confirm_password='testing111', desired_account_type='TRAVEL GUIDE'
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
        self.test_register_admin()
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

    def test_approve_admin_account_type(self):
        self.test_register_admin()
        response = self.client.get('/manage_account_type_permission_request/1/approve')
        self.assertEqual(response.status_code, 200)
        self.assertMessageFlashed(
            'You have just approved request from Test User to give them ADMIN permissions.'
        )

    def test_approve_travel_guide_account_type(self):
        self.test_register_travel_guide()
        response = self.client.get('/manage_account_type_permission_request/1/approve')
        self.assertEqual(response.status_code, 200)
        self.assertMessageFlashed(
            'You have just approved request from Test User to give them TRAVEL GUIDE permissions.'
        )

    def test_reject_account_type_permission_request(self):
        self.test_register_admin()
        response = self.client.get('/manage_account_type_permission_request/1/reject')
        self.assertEqual(response.status_code, 200)
        self.assertMessageFlashed(
            'You have just rejected request from Test User to give them ADMIN permissions.'
        )

    def test_admin_login(self):
        self.test_approve_admin_account_type()
        self.test_login_page_post_recognized_user()

    def test_loading_user_edit_page(self):
        response = self.client.get('/edit_user_data/1')
        self.assertEqual(response.status_code, 200)

    def test_edit_user_data_post_request(self):
        self.test_register_admin()
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

    def test_insert_new_travel_arrangement_no_travel_guides_in_db(self):
        response = self.client.post('/insert_new_arrangement', data=dict(
            destination='Spain', start_date='2021-11-01', end_date='2021-11-10', description='Autumn in Spain.',
            number_of_persons=2, price=580.00
        ))
        self.assertEqual(response.status_code, 302)
        arrangement = Arrangement.query.filter_by(description='Autumn in Spain.').first()
        self.assertEqual(arrangement.id, 1)
        self.assertEqual(arrangement.start_date, date(2021, 11, 1))
        self.assertEqual(arrangement.end_date, date(2021, 11, 10))
        self.assertEqual(arrangement.number_of_persons, 2)
        self.assertEqual(arrangement.price, 580.00)
        self.assertEqual(arrangement.travel_guide_id, None)

    def test_insert_new_travel_arrangement_wo_travel_guide(self):
        response = self.client.post('/insert_new_arrangement', data=dict(
            destination='Spain', start_date='2021-11-01', end_date='2021-11-10', description='Autumn in Spain.',
            number_of_persons=2, price=580.00, travel_guide='None'
        ))
        self.assertEqual(response.status_code, 302)
        arrangement = Arrangement.query.filter_by(description='Autumn in Spain.').first()
        self.assertEqual(arrangement.id, 1)
        self.assertEqual(arrangement.start_date, date(2021, 11, 1))
        self.assertEqual(arrangement.end_date, date(2021, 11, 10))
        self.assertEqual(arrangement.number_of_persons, 2)
        self.assertEqual(arrangement.price, 580.00)
        self.assertEqual(arrangement.travel_guide_id, None)

    def test_insert_new_travel_arrangement_with_travel_guides(self):
        self.test_approve_admin_account_type()
        self.test_register_two_travel_guides()
        # assign two users who are tourist by default, and want to be travel guides to be travel guides
        tourists = User.query.filter_by(account_type='TOURIST').all()
        self.assertEqual(len(tourists), 2)

        tourists[0].account_type = 'TRAVEL GUIDE'
        db.session.add(tourists[0])
        db.session.commit()
        tourists[1].account_type = 'TRAVEL GUIDE'
        db.session.add(tourists[1])
        db.session.commit()

        response = self.client.post('/insert_new_arrangement', data=dict(
            destination='Spain', start_date='2021-11-01', end_date='2021-11-10', description='Autumn in Spain.',
            number_of_persons=4, price=580.00, travel_guide_id=2
        ))

        # force travel_guide_id=2 to be travel guide for arrangement_id=1
        # because we removed inserting travel guide when inserting arrangement
        arrangement = Arrangement.query.filter_by(id=1).first()
        arrangement.travel_guide_id = 2
        db.session.add(arrangement)
        db.session.commit()

        self.assertEqual(response.status_code, 302)
        arrangement = Arrangement.query.filter_by(description='Autumn in Spain.').first()
        self.assertEqual(arrangement.id, 1)
        self.assertEqual(arrangement.start_date, date(2021, 11, 1))
        self.assertEqual(arrangement.end_date, date(2021, 11, 10))
        self.assertEqual(arrangement.number_of_persons, 4)
        self.assertEqual(arrangement.price, 580.00)

    def test_edit_arrangement_page(self):
        self.test_insert_new_travel_arrangement_no_travel_guides_in_db()
        response = self.client.get('/edit_arrangement/1')
        self.assertEqual(response.status_code, 200)

    def test_edit_travel_arrangement(self):
        self.test_insert_new_travel_arrangement_no_travel_guides_in_db()
        response = self.client.post('/edit_arrangement/1', data=dict(
            destination='Spain', start_date='2021-11-05', end_date='2021-11-11', description='Tenerife',
            number_of_persons=3, price=1020.00
        ))
        self.assertEqual(response.status_code, 200)
        arrangement = Arrangement.query.filter_by(id=1).first()
        self.assertEqual(arrangement.start_date, date(2021, 11, 5))
        self.assertEqual(arrangement.end_date, date(2021, 11, 11))
        self.assertEqual(arrangement.description, 'Tenerife')
        self.assertEqual(arrangement.number_of_persons, 3)
        self.assertEqual(arrangement.price, 1020.00)

    def test_cancel_arrangement(self):
        self.test_insert_new_travel_arrangement_no_travel_guides_in_db()
        response = self.client.get('/cancel_arrangement/1')
        arrangement = Arrangement.query.filter_by(id=1).first()
        self.assertEqual(arrangement.status, 'inactive')
        self.assertEqual(response.status_code, 302)

    def test_get_available_travel_guides_ids_method(self):
        # insert two travel guides Travel Guide 1 and Travel Guide 2
        # Assign Travel Gide 2 to the arrangement for period (2021-11-01 - 2021-11-10)
        self.test_insert_new_travel_arrangement_with_travel_guides()
        available_guides = User.get_available_travel_guides_ids('2021-10-01', '2021-10-15')
        self.assertEqual(len(available_guides), 2)  # check if both travel guides are free
        self.assertEqual(f'{available_guides[0].first_name} {available_guides[0].last_name}', 'Travel Guide 1')
        self.assertEqual(f'{available_guides[1].first_name} {available_guides[1].last_name}', 'Travel Guide 2')

        available_guides = User.get_available_travel_guides_ids('2021-10-01', '2021-11-15')
        self.assertEqual(len(available_guides), 1)  # only one travel guide needs to be free
        # that guide is Travel Guide 2
        self.assertEqual(f'{available_guides[0].first_name} {available_guides[0].last_name}', 'Travel Guide 2')

        # insert a new travel arrangement and assign that arrangement to the only available guide (Travel Guide 2 id=3)
        self.client.post('/insert_new_arrangement', data=dict(
            destination='Russia', start_date='2021-10-30', end_date='2021-11-11', description='Russia travel desc.',
            number_of_persons=2, price=1058.00
        ))
        # force travel_guide_id=2 to be travel guide for arrangement_id=1
        # because we removed inserting travel guide when inserting arrangement
        arrangement = Arrangement.query.filter_by(id=2).first()
        arrangement.travel_guide_id = 3
        db.session.add(arrangement)
        db.session.commit()

        available_guides = User.get_available_travel_guides_ids('2021-11-08', '2021-12-15')
        self.assertEqual(len(available_guides), 0)  # there should be no available guide

        available_guides = User.get_available_travel_guides_ids('2022-01-08', '2022-01-30')
        self.assertEqual(len(available_guides), 2)  # there should be no available guide

    @unittest.mock.patch('flask_login.utils._get_user')
    def test_reservations_page(self, current_user):
        mock_user = MagicMock()
        mock_user.id = 1
        # assign mock_user to be current_user in testing environment
        current_user.return_value = mock_user
        response = self.client.get('/reservations')
        self.assertEqual(response.status_code, 200)

    def test_create_reservation_page(self):
        self.test_insert_new_travel_arrangement_with_travel_guides()
        response = self.client.get('/create_reservation/1')
        self.assertEqual(response.status_code, 200)

    def test_create_new_reservation_with_more_person_than_defined_in_arrangement(self):
        self.client.post('/insert_new_arrangement', data=dict(
            destination='Serbia', start_date='2022-08-01', end_date='2022-09-10', description='Serbia summer.',
            number_of_persons=2, price=280.00
        ))
        response = self.client.post('/create_reservation/1', data=dict(number_of_persons=3))
        self.assertEqual(response.status_code, 302)
        self.assertMessageFlashed(
            'You cannot book reservation with number of persons greater than arrangement number of persons.'
        )

    def test_create_new_reservation(self):
        self.test_insert_new_travel_arrangement_with_travel_guides()
        response = self.client.post('/create_reservation/1', data=dict(number_of_persons=4))
        self.assertEqual(response.status_code, 302)
        all_reservations = Reservation.query.all()
        self.assertEqual(len(all_reservations), 1)
        reservation = Reservation.query.filter_by(id=1).first()
        self.assertEqual(reservation.number_of_persons, 4)
        self.assertEqual(reservation.price, 3*580 + 580*0.9)

    def test_all_unbooked_arrangements(self):
        self.test_create_new_reservation()
        # test method without passing any parameter
        unbooked_arrangements = Arrangement.get_all_unbooked_arrangements()
        self.assertEqual(len(unbooked_arrangements.items), 0)
        # insert one more arrangement for Spain
        self.client.post('/insert_new_arrangement', data=dict(
            destination='Spain 2', start_date='2022-08-01', end_date='2022-09-10', description='Spain summer.',
            number_of_persons=2, price=1080.00
        ))
        # test method with passing only destination='Spain'
        unbooked_arrangements = Arrangement.get_all_unbooked_arrangements(destination='Spain')
        self.assertEqual(len(unbooked_arrangements.items), 1)

        # test method with passing only destination='Sp'
        unbooked_arrangements = Arrangement.get_all_unbooked_arrangements(destination='Spain')
        self.assertEqual(len(unbooked_arrangements.items), 1)

        # test method with passing destination='Spain' and defined start and end date
        unbooked_arrangements = Arrangement.get_all_unbooked_arrangements(
            destination='Spain', start_date='2021-01-01', end_date='2021-02-01'
        )
        self.assertEqual(len(unbooked_arrangements.items), 0)

        # test method with passing start and end date without destination
        unbooked_arrangements = Arrangement.get_all_unbooked_arrangements(
            start_date='2021-08-15', end_date='2022-08-25'
        )
        self.assertEqual(len(unbooked_arrangements.items), 1)

    def test_search_users(self):
        response = self.client.get('/search_users?account_type=TOURIST')
        self.assertEqual(response.status_code, 200)

    def test_travel_guide_arrangements(self):
        response = self.client.get('/travel_guide_arrangements/1?page=1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('main/travel_guide_arrangements.html')

    def test_tourist_reservations(self):
        response = self.client.get('/tourist_reservations/1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('main/tourist_reservations.html')


if __name__ == '__main__':
    unittest.main()
