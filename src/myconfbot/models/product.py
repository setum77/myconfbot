from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from .base import Base

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