from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_user, logout_user, login_required

from . import auth
from app.models import User
from app import db
from app.decorators import authenticated_user


def return_message_to_client(message, status_code):
    return jsonify({'message': message}), status_code


@auth.route('/api/v1.0/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json
        user = User.query.filter_by(username=data['username']).first()
        if user is None:
            # There is no user in the database.
            if data['password'] == data['confirm_password']:
                # insert a new user if password and confirmed password are equal
                user = User(
                    first_name=data['first_name'], last_name=data['last_name'], username=data['username'],
                    email=data['email'], password=data['password'], desired_account_type=data['desired_account_type']
                )
                if data['desired_account_type'] in ['TRAVEL GUIDE', 'ADMIN']:
                    user.confirmed_desired_account_type = 'pending'
                db.session.add(user)
                db.session.commit()
                login_user(user)
                msg = 'You have successfully created a new user account. Welcome'
                status_code = 201
            else:
                msg = 'The password that you entered does not match with confirmed password. Please try again'
                status_code = 401
        else:
            msg = 'The username that you have just entered already exists in the database.'
            status_code = 409

        return return_message_to_client(msg, status_code)
    else:
        return return_message_to_client('Method Not Allowed', 405)


@auth.route('/api/v1.0/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        form = request.authorization
        user = User.query.filter_by(username=form['username']).first()
        if user is None:
            msg = 'There is no account with the username that you entered. '
            msg += 'Please check your username or register a new account.'
            status_code = 401
        elif user.verify_password(form['password']):
            login_user(user)
            msg = 'You have successfully login. Welcome!'
            status_code = 200
        else:
            msg = 'Incorrect username or password!'
            status_code = 401

        return return_message_to_client(msg, status_code)
    else:
        return return_message_to_client('Method Not Allowed', 405)


@auth.route('/api/v1.0/logout', methods=['POST'])
@authenticated_user
def logout():
    logout_user()
    return return_message_to_client('You have been logged out. Bye!', 200)
