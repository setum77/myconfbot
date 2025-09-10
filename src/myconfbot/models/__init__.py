from datetime import datetime
from enum import Enum
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class OrderStatus(str, Enum):
    NEW = "новый"
    IN_PROGRESS = "в работе"
    READY = "готов к выдаче"
    COMPLETED = "выполнен"
    CANCELLED = "отменен"

class CustomerCharacteristic(str, Enum):
    REGULAR = "постоянный"
    NEW = "новый"
    VIP = "vip"
    PROBLEMATIC = "проблемный"

class Customer(Base):
    __tablename__ = "customers"
    
    id = sa.Column(sa.Integer, primary_key=True)
    telegram_id = sa.Column(sa.BigInteger, unique=True, nullable=False)
    username = sa.Column(sa.String(100))
    first_name = sa.Column(sa.String(100))
    phone = sa.Column(sa.String(20))
    characteristic = sa.Column(sa.Enum(CustomerCharacteristic), 
                             default=CustomerCharacteristic.NEW)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="customer")

class Admin(Base):
    __tablename__ = "admins"
    
    id = sa.Column(sa.Integer, primary_key=True)
    telegram_id = sa.Column(sa.BigInteger, unique=True, nullable=False)
    username = sa.Column(sa.String(100))
    first_name = sa.Column(sa.String(100))
    phone = sa.Column(sa.String(20))
    address = sa.Column(sa.Text)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

class Category(Base):
    __tablename__ = "categories"
    
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)
    description = sa.Column(sa.Text)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)
    description = sa.Column(sa.Text)
    price = sa.Column(sa.Numeric(10, 2), nullable=False)
    photo_file_id = sa.Column(sa.String(255))
    category_id = sa.Column(sa.Integer, sa.ForeignKey("categories.id"))
    is_available = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")

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

class Order(Base):
    __tablename__ = "orders"
    
    id = sa.Column(sa.Integer, primary_key=True)
    customer_id = sa.Column(sa.Integer, sa.ForeignKey("customers.id"), nullable=False)
    status = sa.Column(sa.Enum(OrderStatus), default=OrderStatus.NEW)
    special_requests = sa.Column(sa.Text)
    order_date = sa.Column(sa.DateTime, default=datetime.utcnow)
    ready_date = sa.Column(sa.DateTime)
    total_amount = sa.Column(sa.Numeric(10, 2))
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = sa.Column(sa.Integer, primary_key=True)
    order_id = sa.Column(sa.Integer, sa.ForeignKey("orders.id"), nullable=False)
    product_id = sa.Column(sa.Integer, sa.ForeignKey("products.id"), nullable=False)
    quantity = sa.Column(sa.Integer, nullable=False)
    price = sa.Column(sa.Numeric(10, 2), nullable=False)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")