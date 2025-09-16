from datetime import datetime
import sqlalchemy as sa
from .base import Base

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