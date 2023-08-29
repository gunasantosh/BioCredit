from . import db
from flask_login import UserMixin
from sqlalchemy import Column


class User(db.Model,UserMixin):

    id = Column(db.Integer, primary_key=True)
    username = Column(db.String(20), nullable=False, unique=True)
    name = Column(db.String(200), nullable=False)
    address = Column(db.String(200), nullable=False)
    latitude = Column(db.String(200), nullable=False)
    longitude = Column(db.String(200), nullable=False)
    accuracy = Column(db.String(30),nullable=False)
    role = Column(db.String(50), nullable=False)
    password = Column(db.String(150), nullable=False)

# class captured_image(db.Model):

#     id = Column(db.Integer, autoincrement=True, primary_key=True)
#     image = Column(db.LongText)


