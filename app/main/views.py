from flask import render_template, flash, request
from flask_login import login_required

from . import main
from app.models import User, Arrangement
from app import db
from app.decorators import requires_account_types


@main.route('/')
@login_required
def index():
    return render_template('main/me.html')


@main.route('/admin_panel')
@login_required
@requires_account_types('ADMIN')
def admin_panel():
    return render_template('main/admin.html')


@main.route('/manage_account_type_permission_request/<user_id>/<action>')
@login_required
@requires_account_types('ADMIN')
def manage_account_type_permission_request(user_id, action):
    user = User.query.filter_by(id=user_id).first()
    if user:
        if action == 'approve':
            user.account_type = user.desired_account_type
            user.confirmed_desired_account_type = 'approve'
            flash(f'You have just approved request from {user.first_name} {user.last_name} '
                  f'to give them {user.desired_account_type} permissions.')
        elif action == 'reject':
            user.confirmed_desired_account_type = 'reject'
            flash(
                f'You have just rejected request from {user.first_name} {user.last_name} '
                f'to give them {user.desired_account_type} permissions.'
            )
    db.session.add(user)
    db.session.commit()
    return render_template('main/admin.html')


@main.route('/edit_user_data/<user_id>', methods=['GET', 'POST'])
@login_required
def edit_user_data(user_id):
    user = User.query.filter_by(id=user_id).first()
    if request.method == 'POST':
        form = request.form
        user.first_name = form['first_name']
        user.last_name = form['last_name']
        user.username = form['username']
        user.email = form['email']
        user.desired_account_type = form['desired_account_type']
        user.confirmed_desired_account_type = 'pending'
        db.session.add(user)
        db.session.commit()
        flash('You have just changed your profile data.')
    return render_template('main/edit_user_data.html', user=user)


@main.route('/arrangements', methods=['GET', 'POST'])
@login_required
@requires_account_types('ADMIN', 'TRAVEL GUIDE')
def arrangements():
    form = request.form
    if request.method == 'POST':
        arrangement = Arrangement(
            destination=form['destination'], start_date=form['start_date'], end_date=form['end_date'],
            description=form['description'], number_of_persons=form['number_of_persons'], price=form['price']
        )
        db.session.add(arrangement)
        db.session.commit()
        flash('You have successfully inserted a new travel arrangement.')
    arrangements = Arrangement.query.all()
    return render_template('main/arrangements.html', arrangements=arrangements)
