from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from enum import Enum
from .base import Base

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