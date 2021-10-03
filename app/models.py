from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
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


class Arrangement(db.Model):
    __tablename__ = 'arrangement'
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    destination = db.Column(db.String(50), nullable=False)
    number_of_persons = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(9, 2), nullable=False)
