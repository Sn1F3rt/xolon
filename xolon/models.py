from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from xolon.factory import db


Base = declarative_base()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, index=True)
    password = db.Column(db.String(120))
    register_date = db.Column(db.DateTime, server_default=func.now())
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    wallet_password = db.Column(db.String(120), nullable=True)
    wallet_created = db.Column(db.Boolean, default=False)
    wallet_connected = db.Column(db.Boolean, default=False)
    wallet_port = db.Column(db.Integer, nullable=True)
    wallet_container = db.Column(db.String(30), nullable=True)
    wallet_start = db.Column(db.DateTime, nullable=True)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def clear_wallet_data(self, reset_password=False, reset_wallet=False):
        self.wallet_connected = False
        self.wallet_port = None
        self.wallet_container = None
        self.wallet_start = None
        if reset_password:
            self.wallet_password = None
        if reset_wallet:
            self.wallet_created = False
        db.session.commit()

    def __repr__(self):
        return self.email


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(60))
    user = db.Column(db.Integer, db.ForeignKey(User.id))
    date = db.Column(db.DateTime, server_default=func.now())

    def __repr__(self):
        return self.id
