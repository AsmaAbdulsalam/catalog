import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    """
    Registered user information is stored in db
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Bookstore(Base):
    """
    Bookstore information is stored in db
    each Bookstore has a unique id
    name and id of the user who created this bookstore
    which makes it has a relationship wiht user table
    """
    __tablename__ = 'bookstore'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class StoreItem(Base):
    """
    StoreItem information is stored in db
    each item sotred in the db has a unique id
    name and id of the user who created this item
    which makes it has a relationship wiht user table
    """
    __tablename__ = 'store_item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    price = Column(String(8))
    category = Column(String(250))
    bookstore_id = Column(Integer, ForeignKey('bookstore.id'))
    bookstore = relationship(Bookstore)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,
            'category': self.category,
        }


engine = create_engine('sqlite:///bookstorelistwithusers.db')
Base.metadata.create_all(engine)
