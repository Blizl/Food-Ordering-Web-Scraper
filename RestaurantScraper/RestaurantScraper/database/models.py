from sqlalchemy import Column, Text, String, Integer
from database.connection import Base


class Restaurant(Base):
    __tablename__ = "Restaurants"
    link = Column(String(120), unique=False)
    name = Column(String(120), unique=False)
    menu = Column(Text, unique=False)
    zipcode = Column(String(32), unique=False)
    city = Column(String(120), unique=False)
    rest_id = Column(Integer, primary_key=True)

    def __init__(self, menu=None, link=None, name=None, zipcode=None, city=None, rest_id=None):
        self.name = name
        self.link = link
        self.menu = menu
        self.zipcode = zipcode
        self.city = city
        self.id = rest_id

    def __repr__(self):
        return '<Restaurant> %r in %r' % (self.name, self.city)
