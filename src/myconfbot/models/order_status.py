from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from .base import Base

class OrderStatus(Base):
    __tablename__ = "order_statuses"
    
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)  # character varying
    description = sa.Column(sa.Text)  # может быть NULL
    
    # Связь с заказами
    #orders = relationship("Order", back_populates="status")