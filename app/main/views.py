from datetime import date, timedelta

from flask import render_template, request, jsonify
from flask_login import current_user
from flask_mail import Message
from sqlalchemy.exc import IntegrityError
from . import main
from app.models import User, Arrangement, Reservation
from app import db, mail
from app.decorators import requires_account_types, authenticated_user


def return_message_to_client(message, status_code):
    return jsonify({'message': message}), status_code


@main.app_errorhandler(405)
def method_not_allowed(e):
    return return_message_to_client('Method Not Allowed!', 405)


@main.route('/api/v1.0/users', methods=['GET'])
@authenticated_user
@requires_account_types('ADMIN')
def get_all_users():
    users = User.get_all_json()
    return jsonify(users)


@main.route('/api/v1.0/my_data', methods=['GET', 'PUT'])
@authenticated_user
def my_data():
    user = User.get_user_by_id(current_user.id)

    if request.method == 'GET':
        return jsonify(user)

    elif request.method == 'PUT':
        if request.json is None:
            msg = 'Request that you send does not have any data. '
            msg += 'Please send json with new value of your data as a user.'
            return return_message_to_client(msg, 400)
        # change user's data
        user = User.query.filter_by(id=current_user.id).first()
        updated_all_fields = user.update_data(**request.json)
        if updated_all_fields is False:
            msg = 'Please chose one of the following desired_account_type: ADMIN, TOURIST, TRAVEL GUIDE.'
            status_code = 400
        elif updated_all_fields is None:
            msg = 'TRAVEL GUIDE cannot send request for changing their account type to TOURIST.'
            status_code = 400
        else:
            msg = 'You have successfully changed your data.'
            status_code = 200

    return return_message_to_client(msg, status_code)


@main.route('/api/v1.0/account_type_requests', methods=['GET'])
@authenticated_user
@requires_account_types('ADMIN')
def account_type_requests():
    page = int(request.args.get('page', 1))
    requests = User.get_pending_account_type_requests(page=page)
    return jsonify(requests)


@main.route('/api/v1.0/account_type_requests/<user_id>/<action>', methods=['PUT'])
@authenticated_user
@requires_account_types('ADMIN')
def manage_account_type_permission_request(user_id, action):

    if action not in ['approved', 'rejected']:
        msg = 'You need to use /<user_id>/approved or <user_id>/rejected as arguments in order to resolve the request.'
        status_code = 400
        return return_message_to_client(msg, status_code)

    user = User.query.filter_by(id=user_id).first()
    if user:

        if user.account_type == user.desired_account_type:
            msg = 'This user did not send request or their request has been already resolved.'
            status_code = 400
            return return_message_to_client(msg, status_code)

        previous_account_type = user.account_type  # store this info in order to revert back if mail is not sent
        previous_confirmed_desired_account_type = user.confirmed_desired_account_type  # same as previous acc type

        if action == 'approved':
            user.account_type = user.desired_account_type
            user.confirmed_desired_account_type = 'approve'
            msg = f'You have just approved request from {user.first_name} {user.last_name} '
            msg += f' to give them {user.desired_account_type} permissions.'
        elif action == 'rejected':
            user.confirmed_desired_account_type = 'reject'
            msg = f'You have just rejected request from {user.first_name} {user.last_name} '
            msg += f'to give them {user.desired_account_type} permissions.'
        try:
            message = Message(
                f"{action.capitalize()} {user.desired_account_type} account type",
                recipients=[user.email]
            )
            message.body = render_template(
                'mail/account_type_request.txt', user=user, action=action
            )
            mail.send(message)
        except Exception as e:
            user.account_type = previous_account_type
            user.confirmed_desired_account_type = previous_confirmed_desired_account_type
            print(e)
    db.session.add(user)
    db.session.commit()
    status_code = 200

    return return_message_to_client(msg, status_code)


@main.route('/api/v1.0/arrangements', methods=['GET'])
def arrangements():
    if current_user.is_anonymous:
        arrangements = Arrangement.get_basic_arrangements_info()
        return jsonify(arrangements)
    page = int(request.args.get('page', 1))
    columns_order = request.args.get('columns_order')
    creator_id = request.args.get('creator_id')  # TODO: Put in creator_id currently logged in user
    creator_id = 1

    arrangements = Arrangement.get_all_travel_arrangements(page=page, columns_order=columns_order)
    if arrangements is None:
        # user did not send correct sort by argument
        msg = 'If you want to sort arrangements please use ?columns_order=column_name asc/desc'
        return return_message_to_client(msg, 400)
    return jsonify(arrangements)


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


@main.route('/api/v1.0/arrangements/<arrangement_id>', methods=['PUT'])
@authenticated_user
@requires_account_types('ADMIN', 'TRAVEL GUIDE')
def update_arrangement(arrangement_id):
    arrangement = Arrangement.query.filter_by(id=arrangement_id).first()
    if arrangement is None:
        msg = 'Arrangement that you are trying to update does not exist!'
        return return_message_to_client(msg, 404)

    if current_user.account_type == 'ADMIN' and arrangement.created_by != current_user.id:
        msg = f'Only creator of the arrangement id {arrangement.id} can update it!'
        return return_message_to_client(msg, 404)

    five_days_after_today = date.today() + timedelta(days=5)
    if five_days_after_today > arrangement.start_date:
        msg = f'It is too late to edit arrangement id={arrangement.id} because start date of the arrangement is {arrangement.start_date}.'
        return return_message_to_client(msg, 404)

    data = request.json
    if not data:
        return return_message_to_client('You need to send json data in order to update arrangement.', 400)

    if current_user.account_type == 'ADMIN':
        for field in data:
            if hasattr(arrangement, field):
                if field == 'travel_guide_id':
                    # if travel guide is chosen in insert a new travel arrangement use that value
                    # if user did not chose travel guide that means that we get 'None' string from the client
                    travel_guide_id = data['travel_guide_id'] if data['travel_guide_id'] != 'None' else None

                    # check to see if travel guide is available
                    available_guides_ids = User.get_available_travel_guides_ids(
                        start_travel_date=arrangement.start_date, end_travel_date=arrangement.end_date
                    )
                    guide = User.query.filter_by(id=travel_guide_id).first()
                    if guide and travel_guide_id not in available_guides_ids:
                        msg = f'Travel guide {guide.first_name} {guide.last_name} is not available in this period.'
                        msg += 'Check available guides at /api/v1.0/available_guides route with GET method'
                        return return_message_to_client(msg, 400)

                    try:
                        setattr(arrangement, 'travel_guide_id', travel_guide_id)
                    except IntegrityError as e:
                        # user is trying to update the arrangement with travel_guide which does not exist
                        print(e)  # print this in log file in order to see that Integrity error has occurred
                        msg = 'You are trying to assign travel_guide who does not exist in the database.'
                        return return_message_to_client(msg, 400)
                else:
                    setattr(arrangement, field, data[field])
    elif current_user.account_type == 'TRAVEL GUIDE':
        if arrangement.travel_guide_id != current_user.id:
            msg = 'You do not have permission to edit this arrangement.'
            msg += 'You can only edit arrangement where you are assigned to be a travel guide.'
            return return_message_to_client(msg, 400)
        if 'description' not in data:
            msg = 'You only have permission to edit description of this arrangement.'
            return return_message_to_client(msg, 400)

    db.session.add(arrangement)
    db.session.commit()
    msg = f'You have just successfully changed data for the travel arrangement id {arrangement.id}'
    return return_message_to_client(msg, 200)


@main.route('/api/v1.0/search_arrangements', methods=['GET'])
@authenticated_user
def search_arrangements():
    arrangements = Arrangement.get_all_unbooked_arrangements(**request.args)
    return jsonify(arrangements)


@main.route('/api/v1.0/cancel_arrangement/<arrangement_id>', methods=['PUT'])
@authenticated_user
@requires_account_types('ADMIN')
def cancel_arrangement(arrangement_id):
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


@main.route('/api/v1.0/available_guides')
@authenticated_user
@requires_account_types('ADMIN')
def available_guides():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if not start_date or not end_date:
        # start_date/end_date will be None if there is no args
        msg = 'You need to send get request by adding start_date and end_date'
        msg += '-> /api/v1.0/available_guides?start_date=01.10.2021&end_date=01.12.2021'
        return return_message_to_client(msg, 400)
    available_guides = User.get_available_travel_guides_json(
        start_travel_date=start_date, end_travel_date=end_date
    )
    return jsonify(available_guides)


@main.route('/api/v1.0/travel_guide_arrangements', methods=['GET'])
@authenticated_user
@requires_account_types('TRAVEL GUIDE')
def travel_guide_arrangements():
    page = request.args.get('page', 1, type=int)
    guide_arrangements = Arrangement.get_travel_guide_arrangements(current_user.id, page=page)
    return jsonify(guide_arrangements)


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

    for field in ['arrangement_id', 'number_of_persons']:
        if field not in data:
            msg = f'You need to send {field} in order to create reservation'
            return return_message_to_client(msg, 400)

    number_of_persons = int(data['number_of_persons'])
    arrangement_id = int(data['arrangement_id'])
    arrangement = Arrangement.query.filter_by(id=arrangement_id).first()

    for reservation in arrangement.reservations:
        if reservation.user_id == current_user.id:
            # currently logged in user(tourist) already have reservation for this arrangement
            msg = f'You already have reservation for this arrangement - {arrangement.destination}'
            return return_message_to_client(msg, 400)

    # check to see it it is too late to create reservation for this arrangement
    if date.today() + timedelta(days=5) > arrangement.start_date:
        msg = "It is too late to create reservation for this arrangement since it starts on "
        msg += f"{arrangement.start_date.strftime('%d.%m.%Y')}"
        status_code = 400
        return return_message_to_client(msg, status_code)

    unbooked_number_of_reservation = (arrangement.number_of_persons - arrangement.reserved_number_of_persons)
    if number_of_persons > arrangement.number_of_persons:
        msg = 'You cannot book reservation with number of persons greater than '
        msg += f'remaining {unbooked_number_of_reservation} unbooked reservation(places).'
        status_code = 400
    elif number_of_persons > unbooked_number_of_reservation:
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