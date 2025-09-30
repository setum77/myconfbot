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
    cover_photo_path = sa.Column(sa.String(255))
    short_description = sa.Column(sa.Text)
    is_available = sa.Column(sa.Boolean, default=True)
    measurement_unit = sa.Column(sa.String(50))
    quantity = sa.Column(sa.Numeric(10, 2), default=0)
    price = sa.Column(sa.Numeric(10, 2), nullable=False)
    prepayment_conditions = sa.Column(sa.Text)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = relationship("Category", back_populates="products")
    photos = relationship("ProductPhoto", back_populates="product", lazy="select")
    orders = relationship("Order", back_populates="product")

    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', price={self.price})"
    
class ProductPhoto(Base):
    __tablename__ = "product_photos"
    
    id = sa.Column(sa.Integer, primary_key=True)
    product_id = sa.Column(sa.Integer, sa.ForeignKey("products.id"), nullable=False)
    photo_path = sa.Column(sa.String(255), nullable=False)
    caption = sa.Column(sa.String(200))
    order_index = sa.Column(sa.Integer, default=0)
    alt_text = sa.Column(sa.String(100))
    is_main = sa.Column(sa.Boolean, default=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="photos")

class OrderStatusEnum(Enum):
    CREATED = "Создан / Новый"
    CONFIRMED = "Подтверждён"
    IN_PROGRESS = "В работе / Готовится"
    AWAITING_DECORATION = "Ожидает украшения / Декорирования"
    READY_FOR_PICKUP = "Готов к выдаче / Упакован"
    IN_DELIVERY = "Передан курьеру / В доставке"
    COMPLETED = "Выполнен / Завершён"
    CANCELLED = "Отменён"
    ON_HOLD = "Отложен / На паузе"
    PROBLEMATIC = "Проблемный / Требует внимания"

class OrderStatus(Base):
    __tablename__ = "order_statuses"
    
    id = sa.Column(sa.Integer, primary_key=True)
    order_id = sa.Column(sa.Integer, sa.ForeignKey("orders.id"), nullable=False)
    status = sa.Column(sa.String(100), nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    photo_path = sa.Column(sa.String(255))
    
    order = relationship("Order", back_populates="status_history")

class Order(Base):
    __tablename__ = "orders"
    
    id = sa.Column(sa.Integer, primary_key=True)
    #user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.telegram_id"), nullable=False)
    delivery_address = sa.Column(sa.Text)
    product_id = sa.Column(sa.Integer, sa.ForeignKey("products.id"), nullable=False)
    weight_grams = sa.Column(sa.Integer)
    quantity = sa.Column(sa.Integer)
    delivery_type = sa.Column(sa.String(50))
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    ready_at = sa.Column(sa.DateTime)
    total_cost = sa.Column(sa.Numeric(10, 2))
    executor_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    payment_type = sa.Column(sa.String(50))
    payment_status = sa.Column(sa.String(50))
    admin_notes = sa.Column(sa.Text)  # Пометки к заказу (заполняет админ)
    
    # Связи
    user = relationship("User", foreign_keys=[user_id])
    product = relationship("Product", back_populates="orders")
    executor = relationship("User", foreign_keys=[executor_id])
    status_history = relationship("OrderStatus", back_populates="order")
    notes = relationship("OrderNote", back_populates="order")

class OrderNote(Base):
    __tablename__ = "order_notes"
    
    id = sa.Column(sa.Integer, primary_key=True)
    order_id = sa.Column(sa.Integer, sa.ForeignKey("orders.id"), nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    #user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.telegram_id"), nullable=False)
    note_text = sa.Column(sa.Text, nullable=False)
    
    order = relationship("Order", back_populates="notes")
    user = relationship("User")

class User(Base):
    __tablename__ = "users"
    
    id = sa.Column(sa.Integer, primary_key=True)
    telegram_id = sa.Column(sa.BigInteger, unique=True, nullable=False)
    telegram_username = sa.Column(sa.String(100))
    full_name = sa.Column(sa.String(200))
    phone = sa.Column(sa.String(20))
    address = sa.Column(sa.Text)
    characteristics = sa.Column(sa.Text)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    is_admin = sa.Column(sa.Boolean, default=False)
    photo_path = sa.Column(sa.String(500))
    
    orders = relationship("Order", back_populates="user", foreign_keys=[Order.user_id])
    executed_orders = relationship("Order", back_populates="executor", foreign_keys=[Order.executor_id])
    order_notes = relationship("OrderNote", back_populates="user")