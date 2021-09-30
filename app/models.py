from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    confirmed_password = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.Enum('ADMIN', 'TRAVEL GUIDE', 'TOURIST', name='account_type'), nullable=False)
