from functools import wraps

from flask import flash, redirect, url_for, current_app, jsonify
from flask_login import current_user

import app


def return_message_to_client(message, status_code):
    return jsonify({'message': message}), status_code


def get_current_user_account_type():
    if current_app.config['LOGIN_DISABLED']:
        return 'ADMIN'
    try:
        return current_user.account_type
    except:
        flash("Please login.")
        return redirect(url_for('auth.login'))


def requires_account_types(*account_types):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if get_current_user_account_type() not in account_types:
                return return_message_to_client('You do not have the permission to access that page', 401)
            return f(*args, **kwargs)

        return wrapped
    return wrapper


def authenticated_user(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_app.config['TESTING']:
            if not current_user.is_authenticated:
                return return_message_to_client('Unauthenticated user! You need to be logged in.', 401)
        return f(*args, **kwargs)

    return wrapped