from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from .base import Base

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
    #order_items = relationship("OrderItem", back_populates="product")