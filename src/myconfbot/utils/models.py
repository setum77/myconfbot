from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
from sqlalchemy import Numeric

from enum import Enum

Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"
    
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)
    description = sa.Column(sa.Text)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    
    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"Category(id={self.id}, name='{self.name}')"
    
class Product(Base):
    __tablename__ = "products"
    
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)
    category_id = sa.Column(sa.Integer, sa.ForeignKey("categories.id"))
    cover_photo_path = sa.Column(sa.String(255))  # Исправлено
    short_description = sa.Column(sa.Text)  # Добавлено
    price = sa.Column(sa.Numeric(10, 2), nullable=False)
    #photo_file_id = sa.Column(sa.String(255))  # Оставьте, если нужно
    
    is_available = sa.Column(sa.Boolean, default=True)
    measurement_unit = sa.Column(sa.String(50))  # Добавлено
    quantity = sa.Column(sa.Numeric(10, 2), default=0)  # Добавлено
    prepayment_conditions = sa.Column(sa.Text)  # Добавлено
    
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Добавлено
    
    category = relationship("Category", back_populates="products")
    #order_items = relationship("OrderItem", back_populates="product")
    #photos = relationship("ProductPhoto", back_populates="product", cascade="all, delete-orphan")
    photos = relationship("ProductPhoto", back_populates="product", lazy="select")

    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', price={self.price})"
    
class ProductPhoto(Base):
    __tablename__ = "product_photos"
    
    id = sa.Column(sa.Integer, primary_key=True)
    product_id = sa.Column(sa.Integer, sa.ForeignKey("products.id"), nullable=False)
    photo_path = sa.Column(sa.String(255), nullable=False)
    caption = sa.Column(sa.String(200))          # Подпись к фото
    order_index = sa.Column(sa.Integer, default=0)  # Порядок показа (0, 1, 2...)
    alt_text = sa.Column(sa.String(100))
    is_main = sa.Column(sa.Boolean, default=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="photos")
    

class OrderStatus(Base):
    __tablename__ = "order_statuses"
    
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)  # character varying
    description = sa.Column(sa.Text)  # может быть NULL
    
    # Связь с заказами
    #orders = relationship("Order", back_populates="status")

class Order(Base):
    __tablename__ = "orders"
    
    id = sa.Column(sa.Integer, primary_key=True)
    client_name = sa.Column(sa.String(100))
    client_phone = sa.Column(sa.String(20))
    delivery_address = sa.Column(sa.Text)
    product_id = sa.Column(sa.Integer, sa.ForeignKey("products.id"))
    weight_grams = sa.Column(sa.Integer)
    quantity = sa.Column(sa.Integer)
    delivery_type = sa.Column(sa.String(50))
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    ready_at = sa.Column(sa.DateTime)
    comments = sa.Column(sa.Text)
    total_cost = sa.Column(sa.Numeric(10, 2))
    status_id = sa.Column(sa.Integer, sa.ForeignKey("order_statuses.id"))  
    status_changed_at = sa.Column(sa.DateTime)
    status_reason = sa.Column(sa.Text)
    executor_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    payment_type = sa.Column(sa.String(50))
    payment_status = sa.Column(sa.String(50))
    completed_photo_path = sa.Column(sa.String(255))
    
#     # Связи
#     product = relationship("Product")
#     executor = relationship("User", foreign_keys=[executor_id])
#     status = relationship("OrderStatus", back_populates="orders")  

# class OrderItem(Base):
#     __tablename__ = "order_items"
    
#     id = sa.Column(sa.Integer, primary_key=True)
#     order_id = sa.Column(sa.Integer, sa.ForeignKey("orders.id"), nullable=False)
#     product_id = sa.Column(sa.Integer, sa.ForeignKey("products.id"), nullable=False)
#     quantity = sa.Column(sa.Integer, nullable=False)
#     price = sa.Column(sa.Numeric(10, 2), nullable=False)
    
#     order = relationship("Order", back_populates="items")
#     product = relationship("Product", back_populates="order_items")
    
class Recipe(Base):
    __tablename__ = "recipes"
    
    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.String(200), nullable=False)
    description = sa.Column(sa.Text)
    ingredients = sa.Column(sa.Text, nullable=False)
    instructions = sa.Column(sa.Text, nullable=False)
    photo_file_id = sa.Column(sa.String(255))
    cooking_time = sa.Column(sa.Integer)  # in minutes
    difficulty = sa.Column(sa.String(50))
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)



class User(Base):
    __tablename__ = "users"
    
    id = sa.Column(sa.Integer, primary_key=True)
    telegram_id = sa.Column(sa.BigInteger, unique=True, nullable=False)
    telegram_username = sa.Column(sa.String(100))
    full_name = sa.Column(sa.String(100))
    phone = sa.Column(sa.String(20))
    address = sa.Column(sa.Text)
    characteristics = sa.Column(sa.Text)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    is_admin = sa.Column(sa.Boolean, default=False)
    photo_path = sa.Column(sa.String(255))
    
    # orders = relationship("Order", back_populates="user")
