from datetime import date, timedelta
from decimal import Decimal
import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user
from sqlalchemy import and_, or_

from app import db, login_manager


@login_manager.user_loader
def get_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
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

    # travel_guide = db.relationship('Arrangement', foreign_keys='Arrangement.travel_guide_id')

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


class Arrangement(db.Model):
    __tablename__ = 'arrangement'
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    destination = db.Column(db.String(50), nullable=False)
    number_of_persons = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(9, 2), nullable=False)
    status = db.Column(db.Enum('active', 'inactive', name='status'), nullable=True, default='active')
    travel_guide_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    guide = db.relationship('User', foreign_keys=[travel_guide_id], backref='arrangement')

    @classmethod
    def get_all_unbooked_arrangements(cls):
        five_days_after_today = date.today() + timedelta(days=5)
        return cls.query.join(Reservation, Reservation.arrangement_id == cls.id, isouter=True).filter(
            Reservation.user_id == None,
            Arrangement.start_date > five_days_after_today
        ).order_by(Arrangement.start_date).all()


class Reservation(db.Model):
    __tablename__ = 'reservation'
    id = db.Column(db.Integer, primary_key=True)
    arrangement_id = db.Column(db.Integer, db.ForeignKey('arrangement.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    number_of_persons = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(9, 2), nullable=False)

    arrangement = db.relationship('Arrangement', foreign_keys=[arrangement_id])
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
            arrangement_id=arrangement.id, user_id=user_id, number_of_persons=number_of_persons, price=price
        )
        db.session.add(reservation)
        db.session.commit()
        return reservation

    @classmethod
    def get_all_my_reservations(cls):
        return cls.query.filter_by()

