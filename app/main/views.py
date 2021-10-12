from datetime import date, timedelta

from flask import render_template, flash, request, redirect, url_for, current_app, jsonify, abort
from flask_login import login_required, current_user
from flask_mail import Message
from sqlalchemy.exc import IntegrityError
from . import main
from app.models import User, Arrangement, Reservation, ITEM_PER_PAGE
from app import db, mail
from app.decorators import requires_account_types, authenticated_user


def return_message_to_client(message, status_code):
    return jsonify({'message': message}), status_code


@main.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return render_template('main/me.html')


@main.route('/api/v1.0/users', methods=['GET', 'POST'])
@authenticated_user
@requires_account_types('ADMIN')
def get_all_users():
    users = User.get_all_json()
    return jsonify(users)


@main.route('/api/v1.0/users/<user_id>', methods=['GET', 'PUT'])
def edit_user_data(user_id):
    user = User.query.filter_by(id=user_id).first()
    if request.method == 'PUT':
        data = request.json
        if data:
            for attr in data:
                setattr(user, attr, data[attr])

            if 'desired_account_type' in data:
                user.desired_account_type = data['desired_account_type']
                user.confirmed_desired_account_type = 'pending'

            db.session.add(user)
            db.session.commit()
            msg = 'You have just changed your profile data.'
            status_code = 200
        else:
            msg = "Request that you send does not have any data. Please send json with new value of your data as a user."
            status_code = 400
    else:
        msg = 'Method Not Allowed!'
        status_code = 405

    return return_message_to_client(msg, status_code)


@main.route('/manage_account_type_permission_request/<user_id>/<action>')
def manage_account_type_permission_request(user_id, action):
    user = User.query.filter_by(id=user_id).first()
    if user:

        previous_account_type = user.account_type  # store this info in order to revert back if mail is not sent
        previous_confirmed_desired_account_type = user.confirmed_desired_account_type  # same as previous acc type

        if action == 'approved':
            user.account_type = user.desired_account_type
            user.confirmed_desired_account_type = 'approve'
            flash(f'You have just approved request from {user.first_name} {user.last_name} '
                  f'to give them {user.desired_account_type} permissions.')
        elif action == 'rejected':
            user.confirmed_desired_account_type = 'reject'
            flash(
                f'You have just rejected request from {user.first_name} {user.last_name} '
                f'to give them {user.desired_account_type} permissions.'
            )

        try:
            msg = Message(
                f"{action.capitalize()} {user.desired_account_type} account type",
                recipients=[user.email]
            )
            msg.body = render_template(
                'mail/account_type_request.txt', user=user, action=action
            )
            mail.send(msg)
        except Exception as e:
            user.account_type = previous_account_type
            user.confirmed_desired_account_type = previous_confirmed_desired_account_type
            print(e)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('main.admin_panel'))


@main.route('/api/v1.0/arrangements', methods=['POST'])
@requires_account_types('ADMIN')
def insert_arrangement():

    def all_fields_exist(json_request):
        """"
            :param json_request as request.json from the client
            :returns list of two elements
                - first is True when everything is ok regarding json data existence
                - first is False when some of the data from client are missing
                - second element is message which is only be used in response when some data is missing to inform client
                about missing data
        """
        for field in ['destination', 'description', 'start_date', 'end_date', 'number_of_persons', 'price']:
            if field not in json_request:
                return False, field
        return True, 'OK'  # this is added in order to send some default message when all data has been sent from client

    json = request.json
    if not json or not all_fields_exist(json)[0]:
        non_existing_field = all_fields_exist(json)[1]
        msg = f'{non_existing_field} data is required for creating a new arrangement! '
        msg += 'Please add them in the the HTTP body and send the request again.'
        response = jsonify(
            {'message': msg}
        )
        response.status_code = 400
        return response

    # try to find if there is already arrangement in the database
    arrangement = Arrangement.query.filter_by(
        destination=json['destination'], description=json['description'],
        start_date=json['start_date'], end_date=json['end_date']
    ).first()
    if arrangement:
        msg = 'An arrangement which you have just tried to insert already exist in the database.'
        return return_message_to_client(msg, 400)

    arrangement = Arrangement.insert_new_arrangement(
        destination=json['destination'], description=json['description'],
        start_date=json['start_date'], end_date=json['end_date'], number_of_persons=json['number_of_persons'],
        price=json['price']
    )
    return arrangement, 201


@main.route('/api/v1.0/arrangements', methods=['GET'])
@authenticated_user
def arrangements():
    page = int(request.args.get('page', 1))
    columns_order = request.args.get('columns_order')
    creator_id = request.args.get('creator_id')  # TODO: Put in creator_id currently logged in user
    creator_id = 1

    arrangements = Arrangement.get_all_travel_arrangements(
        page=page, columns_order=columns_order, creator_id=creator_id
    )
    return jsonify(arrangements)


@main.route('/api/v1.0/arrangements/<arrangement_id>', methods=['PUT'])
def update_arrangement(arrangement_id):
    arrangement = Arrangement.query.filter_by(id=arrangement_id).first()
    if arrangement is None:
        msg = 'Arrangement that you are trying to update does not exist!'
        return return_message_to_client(msg, 404)

    if arrangement.created_by != current_user.id:
        msg = f'Only creator of the arrangement id {arrangement.id} can update it!'
        return return_message_to_client(msg, 404)

    five_days_after_today = date.today() + timedelta(days=5)
    if five_days_after_today > arrangement.start_date:
        msg = f'It is too late to edit arrangement id={arrangement.id} because start date of the arrangement is {arrangement.start_date}.'
        return return_message_to_client(msg, 404)

    if request.method == 'PUT':
        data = request.json
        if not data:
            return return_message_to_client('You need to send json data in order to update arrangement.', 400)

        for field in data:
            if hasattr(arrangement, field):
                if field == 'travel_guide_id':
                    # if travel guide is chosen in insert a new travel arrangement use that value
                    # if user did not chose travel guide that means that we get 'None' string from the client
                    travel_guide_id = data['travel_guide_id'] if data['travel_guide_id'] != 'None' else None
                    try:
                        setattr(arrangement, 'travel_guide_id', travel_guide_id)
                    except IntegrityError as e:
                        # user is trying to update the arrangement with travel_guide which does not exist
                        print(e)  # print this in log file in order to see that Integrity error has occurred
                        msg = 'You are trying to assign travel_guide who does not exist in the database.'
                        return return_message_to_client(msg, 400)
                else:
                    setattr(arrangement, field, data[field])

        db.session.add(arrangement)
        db.session.commit()
        msg = f'You have just successfully changed data for the travel arrangement id {arrangement.id}'
        return return_message_to_client(msg, 200)


@main.route('/api/v1.0/cancel_arrangement/<arrangement_id>', methods=['PUT', 'GET', 'POST'])
@authenticated_user
@requires_account_types('ADMIN')
def cancel_arrangement(arrangement_id):
    if request.method == 'PUT':
        arrangement = Arrangement.query.filter_by(id=arrangement_id).first()
        if arrangement is None:
            msg = 'Arrangement that you are trying to cancel does not exist!'
            return return_message_to_client(msg, 404)
        if arrangement.reservations:
            # send email notification only if there is some reservation for this arrangement
            for reservation in arrangement.reservations:
                try:
                    arrangement.status = 'inactive'

                    # send mail notification to inform tourists that arrangement has been deleted
                    msg = Message(
                        f"Travel arrangement ({arrangement.destination} {arrangement.start_date.strftime('%d.%m.%Y')} - {arrangement.end_date.strftime('%d.%m.%Y')}) canceled.",
                        recipients=[arrangement.reservations[0].user.email]
                    )
                    msg.body = render_template('mail/canceled_arrangement.txt', reservation=reservation)
                    mail.send(msg)
                except Exception as e:
                    print(e)
                    # revert back to active if there is some problem with sending email
                    arrangement.status = 'active'
        else:
            arrangement.status = 'inactive'

        db.session.add(arrangement)
        db.session.commit()

        return return_message_to_client(f'You have successfully canceled arrangement id {arrangement.id}', 200)
    else:
        return return_message_to_client('PUT is only allowed method for canceling the arrangement', 405)


@main.route('/api/v1.0/reservations', methods=['GET'])
@authenticated_user
@requires_account_types('ADMIN', 'TOURIST')
def reservations():
    page = int(request.args.get('page', 1))
    columns_order = request.args.get('columns_order', 'id asc')
    reservations = Reservation.get_reservations(
        page=page, columns_order=columns_order
    )
    return jsonify(reservations)


@main.route('/api/v1.0/reservations', methods=['POST'])
@authenticated_user
@requires_account_types('TOURIST')
def create_reservation():
    data = request.json
    number_of_persons = int(data['number_of_persons'])
    arrangement_id = int(data['arrangement_id'])
    arrangement = Arrangement.query.filter_by(id=arrangement_id).first()
    if number_of_persons > arrangement.number_of_persons:
        msg = 'You cannot book reservation with number of persons greater than arrangement number of persons.'
        status_code = 400
    elif number_of_persons > (arrangement.number_of_persons - arrangement.reserved_number_of_persons):
        # there is no available places for this arrangement
        msg = 'You cannot reserve more than currently available places for this arrangement.'
        status_code = 400
    else:
        reservation = Reservation.create_reservation(arrangement, current_user.id, number_of_persons)

        Arrangement.book_reservation(arrangement_id=reservation.arrangement_id, number_of_persons=number_of_persons)

        msg = f'You have successfully created reservation id {reservation.id}'
        status_code = 201
        try:
            email_msg = Message(
                f"Reservation for travel {arrangement.description} successfully created",
                recipients=[current_user.email]
            )
            email_msg.body = render_template(
                'mail/created_reservation.txt', current_user=current_user, reservation=reservation
            )
            mail.send(email_msg)
        except Exception as e:
            print(e)
            msg += ' but notification mail cannot be sent!'
    return return_message_to_client(msg, status_code)


@main.route('/travel_guide_arrangements/<guide_id>')
def travel_guide_arrangements(guide_id):
    page = request.args.get('page', 1, type=int)
    travel_arrangements = Arrangement.get_travel_guide_arrangements(guide_id, page=page)
    guide = User.query.filter_by(id=guide_id).first()
    return render_template(
        'main/travel_guide_arrangements.html', travel_arrangements=travel_arrangements.items, guide=guide
    )


@main.route('/tourist_reservations/<tourist_id>')
def tourist_reservations(tourist_id):
    page = request.args.get('page', 1, type=int)
    tourist_reservations = Reservation.get_tourist_reservations(tourist_id, page=page)
    tourist = User.query.filter_by(id=tourist_id).first()
    return render_template(
        'main/tourist_reservations.html', tourist_reservations=tourist_reservations.items, tourist=tourist
    )


@main.route('/non_registered_user_page')
def non_registered_user_page():
    arrangements = Arrangement.get_all_travel_arrangements()
    return render_template('main/non_registered_user_page.html', arrangements=arrangements)