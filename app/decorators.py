from functools import wraps

from flask import flash, redirect, url_for, current_app
from flask_login import current_user


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
                flash("You don't have the permission to access that page")
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)

        return wrapped
    return wrapper
