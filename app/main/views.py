from datetime import date

from flask import render_template, flash, request, redirect, url_for, current_app
from flask_login import login_required, current_user

from . import main
from app.models import User, Arrangement, Reservation, ITEM_PER_PAGE
from app import db
from app.decorators import requires_account_types


@main.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return render_template('main/me.html')


@main.route('/admin_panel')
@login_required
@requires_account_types('ADMIN')
def admin_panel():
    page = request.args.get('page', 1, type=int)
    columns_order = request.args.get('sort')

    if request.args.get('account_type'):
        account_type = request.args.get('account_type').upper()
        for account in ['TOURIST', 'TRAVEL GUIDE', 'ADMIN']:
            if account_type in account:
                account_type = account
                break
        users = User.get_all_users(page=page, account_type=account_type, columns_order=columns_order)
    else:
        users = User.get_all_users(page=page, columns_order=columns_order)
    has_next = users.has_next
    has_prev = users.has_prev
    next_url = users.next_num if has_next else None
    prev_url = users.prev_num if has_prev else None

    users_pending_requests = User.get_pending_account_type_requests()

    return render_template(
        'main/admin.html',
        next_url=url_for('main.admin_panel', page=next_url),
        prev_url=url_for('main.admin_panel', page=prev_url),
        has_next=has_next, has_prev=has_prev,
        users=users.items, item_per_page=ITEM_PER_PAGE,
        page=page, users_pending_requests=users_pending_requests
    )


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
    return redirect(url_for('main.admin_panel'))


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
        if 'desired_account_type' in form:
            user.desired_account_type = form['desired_account_type']
        user.confirmed_desired_account_type = 'pending'
        db.session.add(user)
        db.session.commit()
        flash('You have just changed your profile data.')
    return render_template('main/edit_user_data.html', user=user)


@main.route('/insert_new_arrangement', methods=['POST'])
@login_required
@requires_account_types('ADMIN')
def insert_new_arrangement():
    if request.method == 'POST':
        form = request.form
        arrangement = Arrangement(
            destination=form['destination'], start_date=form['start_date'], end_date=form['end_date'],
            description=form['description'], number_of_persons=form['number_of_persons'], price=form['price']
        )
        db.session.add(arrangement)
        db.session.commit()
        flash('You have successfully inserted a new travel arrangement.')
    return redirect(url_for('main.arrangements'))


@main.route('/arrangements', methods=['GET'])
def arrangements():
    page = request.args.get('page', 1, type=int)
    columns_order = request.args.get('sort')
    arrangements = Arrangement.get_all_travel_arrangements(page=page, columns_order=columns_order)
    has_next = arrangements.has_next
    has_prev = arrangements.has_prev
    next_url = arrangements.next_num if has_next else None
    prev_url = arrangements.prev_num if has_prev else None

    if current_user.is_authenticated:
        template = 'main/arrangements.html'
    else:
        template = 'main/non_registered_user_page.html'

    return render_template(
        template, current_date=date.today(),
        arrangements=arrangements.items,
        next_url=url_for('main.arrangements', page=next_url, columns_order='start_date asc'),
        prev_url=url_for('main.arrangements', page=prev_url, columns_order='start_date asc'),
        has_next=has_next, has_prev=has_prev, item_per_page=5,
        page=page, columns_order=columns_order
    )


@main.route('/edit_arrangement/<arrangement_id>', methods=['GET', 'POST'])
@login_required
@requires_account_types('ADMIN', 'TRAVEL GUIDE')
def edit_arrangement(arrangement_id):
    arrangement = Arrangement.query.filter_by(id=arrangement_id).first()
    if request.method == 'POST':
        form = request.form
        for field in form:
            if hasattr(arrangement, field):
                if field == 'travel_guide_id':
                    # if travel guide is chosen in insert a new travel arrangement use that value
                    # if user did not chose travel guide that means that we get 'None' string from the client
                    travel_guide_id = form['travel_guide_id'] if form['travel_guide_id'] != 'None' else None
                    setattr(arrangement, 'travel_guide_id', travel_guide_id)
                else:
                    setattr(arrangement, field, form[field])
        db.session.add(arrangement)
        db.session.commit()
        flash(f'You have just successfully changed data for the travel arrangement id {arrangement.id}')
    travel_guides = User.get_available_travel_guides_ids(
        start_travel_date=arrangement.start_date, end_travel_date=arrangement.end_date
    )
    return render_template(
        'main/edit_arrangement.html', arrangement=arrangement, current_date=date.today(), travel_guides=travel_guides
    )


@main.route('/cancel_arrangement/<arrangement_id>')
@login_required
@requires_account_types('ADMIN')
def cancel_arrangement(arrangement_id):
    arrangement = Arrangement.query.filter_by(id=arrangement_id).first()
    arrangement.status = 'inactive'
    db.session.add(arrangement)
    db.session.commit()
    return redirect(url_for('main.arrangements'))


@main.route('/delete_arrangement/<arrangement_id>')
@login_required
@requires_account_types('ADMIN')
def delete_arrangement(arrangement_id):
    arrangement = Arrangement.query.filter_by(id=arrangement_id).first()
    reservation = Reservation.query.filter_by(arrangement_id=arrangement.id).first()
    db.session.delete(reservation)
    db.session.delete(arrangement)
    db.session.commit()
    return redirect(url_for('main.arrangements'))


@main.route('/reservations')
@login_required
def reservations():
    destination = request.args.get('destination')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    arrangements_page = request.args.get('arrangements_page', 1, type=int)
    arrangements = Arrangement.get_all_unbooked_arrangements(
        page=arrangements_page, destination=destination, start_date=start_date, end_date=end_date
    )
    arrangements_next_url = arrangements.next_num if arrangements.has_next else None
    arrangements_prev_url = arrangements.prev_num if arrangements.has_prev else None

    reservations_page = request.args.get('reservations_page', 1, type=int)
    reservations = Reservation.get_tourist_reservations(current_user.id, page=reservations_page)
    reservations_next_url = reservations.next_num if reservations.has_next else None
    reservations_prev_url = reservations.prev_num if reservations.has_prev else None

    return render_template(
        'main/reservations.html',
        arrangements=arrangements.items,
        reservations=reservations.items,

        arrangements_next_url=url_for('main.reservations', arrangements_page=arrangements_next_url),
        arrangements_prev_url=url_for('main.reservations', arrangements_page=arrangements_prev_url),

        reservations_next_url=url_for('main.reservations', reservations_page=reservations_next_url),
        reservations_prev_url=url_for('main.reservations', reservations_page=reservations_prev_url),

        arrangements_has_next=arrangements.has_next, arrangements_has_prev=arrangements.has_prev,
        reservations_has_next=reservations.has_next, reservations_has_prev=reservations.has_prev,

        item_per_page=ITEM_PER_PAGE,
        arrangements_page=arrangements_page,
        reservations_page=reservations_page
    )


@main.route('/create_reservation/<arrangement_id>', methods=['GET', 'POST'])
@login_required
def create_reservation(arrangement_id):
    if request.method == 'POST':
        form = request.form
        number_of_persons = int(form['number_of_persons'])
        arrangement = Arrangement.query.filter_by(id=arrangement_id).first()
        if number_of_persons > arrangement.number_of_persons:
            flash('You cannot book reservation with number of persons greater than arrangement number of persons.')
            return redirect(url_for('main.create_reservation', arrangement_id=arrangement_id))
        else:
            Reservation.create_reservation(arrangement, current_user.id, number_of_persons)
            flash(f'You have successfully created reservation for {arrangement.description}')
            return redirect(url_for('main.reservations'))
    else:
        arrangement = Arrangement.query.filter_by(id=arrangement_id).first()
        return render_template('main/create_reservation.html', arrangement=arrangement)


@main.route('/travel_guide_arrangements/<guide_id>')
@login_required
def travel_guide_arrangements(guide_id):
    page = request.args.get('page', 1, type=int)
    travel_arrangements = Arrangement.get_travel_guide_arrangements(guide_id, page=page)
    return render_template(
        'main/travel_guide_arrangements.html', travel_arrangements=travel_arrangements.items
    )


@main.route('/tourist_reservations/<tourist_id>')
@login_required
def tourist_reservations(tourist_id):
    page = request.args.get('page', 1, type=int)
    tourist_reservations = Reservation.get_tourist_reservations(tourist_id, page=page)
    return render_template(
        'main/tourist_reservations.html', tourist_reservations=tourist_reservations.items
    )


@main.route('/non_registered_user_page')
@login_required
def non_registered_user_page():
    arrangements = Arrangement.get_all_travel_arrangements()
    return render_template('main/non_registered_user_page.html', arrangements=arrangements)