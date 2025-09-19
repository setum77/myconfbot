from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from .base import Base

class ProductPhoto(Base):
    __tablename__ = "product_photos"
    
    id = sa.Column(sa.Integer, primary_key=True)
    product_id = sa.Column(sa.Integer, sa.ForeignKey("products.id"), nullable=False)
    photo_path = sa.Column(sa.String(255), nullable=False)
    is_main = sa.Column(sa.Boolean, default=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    
    product = relationship("Product", backref="photos")