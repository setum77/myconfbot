from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from .base import Base

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