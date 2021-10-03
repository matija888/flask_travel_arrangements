from flask import render_template, flash

from . import main
from app.models import User
from app import db


@main.route('/')
def index():
    return render_template('main/me.html')


@main.route('/manage_account_type_permission_request/<user_id>/<action>')
def manage_account_type_permission_request(user_id, action):
    user = User.query.filter_by(id=user_id).first()
    if user:
        if action == 'approve':
            user.account_type = user.desired_account_type
            db.session.add(user)
            db.session.commit()
            flash(f'You have just approved request from {user.first_name} {user.last_name} '
                  f'to give them {user.desired_account_type} permissions.')
        elif action == 'reject':
            flash(
                f'You have just rejected request from {user.first_name} {user.last_name} '
                f'to give them {user.desired_account_type} permissions.'
            )
    return render_template('main/admin.html')
