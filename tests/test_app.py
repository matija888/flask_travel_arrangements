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

    def test_login_page_post(self):
        response = self.client.post('/auth/login')
        self.assertEqual(response.status_code, 200)

    def test_models(self):
        users = User.query.all()
        self.assertEqual(len(users), 0)

        user = User(
            first_name='John', last_name='Doe', username='john11', password='pass', confirmed_password='pass',
            email='john.doe@example.com', account_type='TOURIST'
        )
        db.session.add(user)
        db.session.commit()

        users = User.query.all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].first_name, 'John')
        self.assertEqual(users[0].last_name, 'Doe')



if __name__ == '__main__':
    unittest.main()
