from flask import render_template, request

from . import auth


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return 'Testing'
    else:
        return render_template('auth/login.html')
