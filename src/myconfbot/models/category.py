from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from .base import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)
    description = sa.Column(sa.Text)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    
    products = relationship("Product", back_populates="category")