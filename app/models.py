from datetime import date, timedelta
from decimal import Decimal
import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user
from sqlalchemy import and_, or_, text
from marshmallow import Schema, fields

from app import db, login_manager


@login_manager.user_loader
def get_user(user_id):
    return User.query.get(int(user_id))


ITEM_PER_PAGE = 5


class DatabaseObject:
    """
    convert_object_to_json_string method converts objects from child classes(User, Arrangement, Reservation etc...)
    into the list which contains JSON formatted strings
    """
    @classmethod
    def convert_object_to_json_string(cls, schema, list):
        result = []
        for item in list:
            marshmallow_item = schema.dump(item)
            result.append(marshmallow_item)
        return result


class User(db.Model, UserMixin, DatabaseObject):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    account_type = db.Column(
        db.Enum('ADMIN', 'TRAVEL GUIDE', 'TOURIST', name='account_type'), nullable=True, default='TOURIST'
    )
    desired_account_type = db.Column(
        db.Enum('ADMIN', 'TRAVEL GUIDE', 'TOURIST', name='desired_account_type'), nullable=False,
    )
    confirmed_desired_account_type = db.Column(
        db.Enum('approve', 'reject', 'pending', name='confirmed_desired_account_type'), nullable=True
    )

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_pending_account_type_requests(cls):
        non_pending_users_list_of_tuples = cls.query.with_entities(cls.id).filter(
            or_(
                and_(
                    cls.account_type == 'ADMIN',
                    cls.desired_account_type == 'ADMIN',
                ),
                and_(
                    cls.account_type == 'TOURIST',
                    cls.desired_account_type == 'TOURIST',
                ),
                and_(
                    cls.account_type == 'TRAVEL GUIDE',
                    cls.desired_account_type == 'TRAVEL GUIDE',
                ),
            )
        ).all()
        non_pending_users_list = [user_id for (user_id, ) in non_pending_users_list_of_tuples]

        return [
            user
            for user in cls.query.all()
            if user.id not in non_pending_users_list and user.confirmed_desired_account_type not in [
                'approve', 'reject'
            ]
        ]

    @classmethod
    def get_available_travel_guides_ids(cls, start_travel_date, end_travel_date):
        """"
            :param start_travel_date
            :param end_travel_date
            :return list of travel guides (User objects) which is available for assigning to arrangement
            which will occur in the period between start_travel_date and end_travel_date
        """
        current_date = datetime.date.today()

        # get ids of users who has been assigned to a certain travel arrangement
        # and period ot that arrangement is overlapping with period between start_travel_date and end_travel_date
        non_available_assigned_guides_ids_tuples = cls.query.with_entities(cls.id)\
            .join(Arrangement, User.id == Arrangement.travel_guide_id, isouter=True)\
            .filter(
                User.account_type == 'TRAVEL GUIDE',
                Arrangement.travel_guide_id != None,
                or_(
                    and_(
                        Arrangement.start_date >= current_date,
                        or_(
                            and_(
                                start_travel_date <= Arrangement.end_date,
                                start_travel_date >= Arrangement.start_date,
                                end_travel_date >= Arrangement.start_date,
                                end_travel_date >= Arrangement.end_date
                            ),
                            and_(
                                start_travel_date <= Arrangement.start_date,
                                start_travel_date <= Arrangement.end_date,
                                end_travel_date >= Arrangement.start_date,
                                end_travel_date <= Arrangement.end_date
                            ),
                            and_(
                                start_travel_date <= Arrangement.start_date,
                                start_travel_date <= Arrangement.end_date,
                                end_travel_date >= Arrangement.start_date,
                                end_travel_date >= Arrangement.end_date,
                            ),
                            and_(
                                start_travel_date >= Arrangement.start_date,
                                start_travel_date <= Arrangement.end_date,
                                end_travel_date >= Arrangement.start_date,
                                end_travel_date <= Arrangement.end_date,
                            )
                        )
                    )
                )
            ).all()
        # convert those list of tuples to list of ids
        non_available_assigned_guides_ids_list = [user_id for (user_id, ) in non_available_assigned_guides_ids_tuples]

        all_guides = cls.query.filter_by(account_type='TRAVEL GUIDE').all()
        available_guides = []
        for guide in all_guides:
            if guide.id not in non_available_assigned_guides_ids_list:
                available_guides.append(guide)

        return available_guides

    @classmethod
    def get_all_users(cls, **kwargs):
        account_type = kwargs.pop('account_type', '')
        page = kwargs.pop('page', '')
        page = 1 if not page else page
        columns_order = kwargs.pop('columns_order') if 'columns_order' in kwargs else None
        if account_type and columns_order:
            return cls.query\
                .filter_by(account_type=account_type)\
                .order_by(text(columns_order))\
                .paginate(page, ITEM_PER_PAGE, False)
        elif account_type:
            return cls.query \
                .filter_by(account_type=account_type) \
                .paginate(page, ITEM_PER_PAGE, False).items
        elif columns_order:
            return cls.query \
                .order_by(text(columns_order)) \
                .paginate(page, ITEM_PER_PAGE, False).items
        else:
            return cls.query.paginate(page, ITEM_PER_PAGE, False).items

    @classmethod
    def get_all_json(cls):
        schema = globals()[cls.__name__ + 'Schema']()
        objs = cls.get_all_users()
        objs_json = cls.convert_object_to_json_string(schema, objs)
        return objs_json


class UserSchema(Schema):
    id =fields.Int()
    first_name = fields.Str()
    last_name = fields.Str()
    email = fields.Str()
    username = fields.Str()


class Arrangement(db.Model, DatabaseObject):
    __tablename__ = 'arrangement'
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    destination = db.Column(db.String(50), nullable=False)
    number_of_persons = db.Column(db.Integer, nullable=False)
    reserved_number_of_persons = db.Column(db.Integer, nullable=True, default=0)
    price = db.Column(db.Numeric(9, 2), nullable=False)
    status = db.Column(db.Enum('active', 'inactive', name='status'), nullable=True, default='active')
    travel_guide_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    guide = db.relationship('User', foreign_keys=[travel_guide_id], backref='arrangement')

    @classmethod
    def get_all_unbooked_arrangements(cls, **kwargs):
        page = kwargs.pop('page', '')
        page = 1 if not page else page
        destination = kwargs.pop('destination', '')
        start_date = kwargs.pop('start_date', '')
        end_date = kwargs.pop('end_date', '')
        # Set the pagination configuration
        five_days_after_today = date.today() + timedelta(days=5)
        if destination and start_date and end_date:
            return cls.query.join(Reservation, Reservation.arrangement_id == cls.id, isouter=True).filter(
                cls.status == 'active',
                Arrangement.start_date >= five_days_after_today
            ).filter(cls.destination.ilike(f'%{destination}%'))\
                .filter(
                    or_(
                        and_(
                            start_date <= Arrangement.end_date,
                            start_date >= Arrangement.start_date,
                            end_date >= Arrangement.start_date,
                            end_date >= Arrangement.end_date
                        ),
                        and_(
                            start_date <= Arrangement.start_date,
                            start_date <= Arrangement.end_date,
                            end_date >= Arrangement.start_date,
                            end_date <= Arrangement.end_date
                        ),
                        and_(
                            start_date <= Arrangement.start_date,
                            start_date <= Arrangement.end_date,
                            end_date >= Arrangement.start_date,
                            end_date >= Arrangement.end_date,
                        ),
                        and_(
                            start_date >= Arrangement.start_date,
                            start_date <= Arrangement.end_date,
                            end_date >= Arrangement.start_date,
                            end_date <= Arrangement.end_date,
                        )
                    )
                ).order_by(Arrangement.start_date)\
                .paginate(page, ITEM_PER_PAGE, False)
        elif destination:
            return cls.query.join(Reservation, Reservation.arrangement_id == cls.id, isouter=True).filter(
                cls.status == 'active',
                Arrangement.start_date > five_days_after_today
            ).filter(cls.destination.ilike(f'%{destination}%')) \
                .order_by(Arrangement.start_date) \
                .paginate(page, ITEM_PER_PAGE, False)
        elif start_date and end_date:
            return cls.query.join(Reservation, Reservation.arrangement_id == cls.id, isouter=True).filter(
                cls.status == 'active',
                Arrangement.start_date >= five_days_after_today
            ).filter(
                or_(
                    and_(
                        start_date <= Arrangement.end_date,
                        start_date >= Arrangement.start_date,
                        end_date >= Arrangement.start_date,
                        end_date >= Arrangement.end_date
                    ),
                    and_(
                        start_date <= Arrangement.start_date,
                        start_date <= Arrangement.end_date,
                        end_date >= Arrangement.start_date,
                        end_date <= Arrangement.end_date
                    ),
                    and_(
                        start_date <= Arrangement.start_date,
                        start_date <= Arrangement.end_date,
                        end_date >= Arrangement.start_date,
                        end_date >= Arrangement.end_date,
                    ),
                    and_(
                        start_date >= Arrangement.start_date,
                        start_date <= Arrangement.end_date,
                        end_date >= Arrangement.start_date,
                        end_date <= Arrangement.end_date,
                    )
                )
            ).order_by(Arrangement.start_date) \
                .paginate(page, ITEM_PER_PAGE, False)
        else:
            return cls.query.join(Reservation, Reservation.arrangement_id == cls.id, isouter=True).filter(
                cls.status == 'active',
                Arrangement.start_date > five_days_after_today
            ).order_by(Arrangement.start_date).paginate(page, ITEM_PER_PAGE, False)

    @classmethod
    def get_travel_guide_arrangements(cls, guide_id, **kwargs):
        page = kwargs.pop('page', '')
        page = 1 if not page else page
        columns_order = kwargs.pop('columns_order') if 'columns_order' in kwargs else None
        if columns_order:
            return cls.query.filter_by(travel_guide_id=guide_id).order_by(text(columns_order)) \
                .paginate(page, ITEM_PER_PAGE, False)
        else:
            return cls.query.filter_by(travel_guide_id=guide_id).paginate(page, ITEM_PER_PAGE, False)

    @classmethod
    def get_all_travel_arrangements(cls, **kwargs):
        page = kwargs.pop('page', '')
        page = 1 if not page else page
        columns_order = kwargs.pop('columns_order') if 'columns_order' in kwargs else None
        creator_id = kwargs.pop('creator_id') if 'creator_id' in kwargs else None

        if columns_order:
            objs = cls.query.order_by(text(columns_order)).paginate(page, ITEM_PER_PAGE, False).items
        else:
            # sort by start_date ASC by default
            objs = cls.query.order_by(cls.start_date).paginate(page, ITEM_PER_PAGE, False).items

        return cls.convert_object_to_json_string(ArrangementSchema(), objs)

    @classmethod
    def book_reservation(cls, arrangement_id, number_of_persons):
        # book places (number_of_persons from reservation) in arrangement
        arrangement = Arrangement.query.filter_by(id=arrangement_id).first()
        arrangement.reserved_number_of_persons += number_of_persons
        db.session.add(arrangement)
        db.session.commit()

    @classmethod
    def insert_new_arrangement(cls, **kwargs):
        destination = kwargs.pop('destination', '')
        description = kwargs.pop('description', '')
        start_date = kwargs.pop('start_date', '')
        end_date = kwargs.pop('end_date', '')
        number_of_persons = kwargs.pop('number_of_persons', '')
        price = kwargs.pop('price', '')
        arrangement = Arrangement(
            destination=destination, start_date=start_date, end_date=end_date, description=description,
            number_of_persons=number_of_persons, price=price, created_by=current_user.id
        )
        db.session.add(arrangement)
        db.session.commit()
        return cls.get_arrangement_json(arrangement_id=arrangement.id)

    @classmethod
    def get_arrangement_json(cls, arrangement_id):
        obj = cls.query.filter_by(id=arrangement_id).first()
        schema = ArrangementSchema()
        return schema.dump(obj)


class ArrangementSchema(Schema):
    id = fields.Int()
    destination = fields.Str()
    description = fields.Str()
    start_date = fields.Date()
    end_date = fields.Date()
    number_of_persons = fields.Int()
    price = fields.Decimal(as_string=True)


class Reservation(db.Model):
    __tablename__ = 'reservation'
    id = db.Column(db.Integer, primary_key=True)
    arrangement_id = db.Column(db.Integer, db.ForeignKey('arrangement.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    number_of_persons = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(9, 2), nullable=False)

    arrangement = db.relationship('Arrangement', foreign_keys=[arrangement_id], backref='reservations')
    user = db.relationship('User', foreign_keys=[user_id])

    @staticmethod
    def discounted_reservations(price, number_of_persons):
        return (price * (number_of_persons - 3)) * Decimal(0.9)

    @classmethod
    def create_reservation(cls, arrangement, user_id, number_of_persons):
        """"
            return: return just created reservation
        """
        if number_of_persons > 3:
            price = arrangement.price * 3 + cls.discounted_reservations(arrangement.price, number_of_persons)
        else:
            price = arrangement.price * number_of_persons
        reservation = Reservation(
            arrangement_id=arrangement.id, user_id=user_id, number_of_persons=number_of_persons, price=price,
        )
        db.session.add(reservation)
        db.session.commit()
        return reservation

    @classmethod
    def get_all_reservations(cls):
        return cls.query.all()

    @classmethod
    def get_tourist_reservations(cls, tourist_id, **kwargs):
        page = kwargs.pop('page', '')
        page = 1 if not page else page
        return cls.query.join(Arrangement)\
            .filter(Arrangement.status == 'active', cls.user_id == tourist_id).paginate(page, ITEM_PER_PAGE, False)

