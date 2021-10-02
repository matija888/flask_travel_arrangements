from flask import render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user

from . import auth
from app.models import User
from app import db


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form = request.form
        user = User.query.filter_by(username=form['username']).first()
        if user is None:
            # There is not user in the database.
            if form['password'] == form['confirm_password']:
                # insert a new user if password and confirmed password are equal
                user = User(
                    first_name=form['first_name'], last_name=form['last_name'], username=form['username'],
                    email=form['email'], password=form['password'], account_type='TOURIST'
                )
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash('You have successfully created a new user account. Welcome')
                return redirect(url_for('main.index'))
            else:
                # redirect back to the login page and inform the user that two passwords do not match
                flash('The password that you entered does not match with confirmed password. Please try again', 'error')
                return render_template('auth/register.html', form=form)
        else:
            flash('The username that you have just entered already exists in the database.')
            return redirect(url_for('auth.register'))
    else:
        return render_template('auth/register.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form = request.form
        user = User.query.filter_by(username=form['username']).first()
        if user is None:
            flash(
                'There is no account with the username that you entered. '
                'Please check your username or register a new account.',
                'error'
            )
            return redirect(url_for('auth.login'))
        elif user.verify_password(form['password']):
            login_user(user)
            flash('You have successfully login. Welcome!')
            return redirect(url_for('main.index'))
        else:
            flash('Incorrect username or password!', 'error')
            return redirect(url_for('auth.login'))
    else:
        return render_template('auth/login.html')


@auth.route('/logout', methods=['GET'])
def logout():
    logout_user()
    flash('You have been logged out. Bye!')
    return redirect(url_for('auth.login'))
