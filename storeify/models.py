from flask import current_app

from sqlalchemy import create_engine, Column, Integer, Boolean, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session

from storeify.db import Base


class Cart(Base):
    __tablename__ = "cart"
    id = Column(Integer, primary_key=True)
    userid = Column(Integer)
    cart_items = relationship("CartItem")
    currency = Column(String)
    total = Column(Integer)


class CartItem(Base):
    __tablename__ = "cartitem"
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('cart.id'))
    product = relationship("Product")
    product_id = Column(Integer, ForeignKey('product.id'))
    quantity = Column(Integer, nullable=False)


class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    # Price in cents
    price = Column(Integer)
    currency = Column(String)
    inventory_count = Column(Integer)
    can_purchase = Column(Boolean)

    def __repr__(self):
        return "<Product(title=%s price=%d inventory_count=%d" % (
            self.title, self.price, self.inventory_count)
