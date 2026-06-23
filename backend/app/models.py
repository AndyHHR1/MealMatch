from sqlalchemy import Column, Integer, String, Text, Boolean
from app.database import Base
import json

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # e.g., "Seco de Pollo"
    description = Column(Text)
    ingredients = Column(Text, nullable=False)  # JSON string list
    steps = Column(Text)  # JSON string list
    prep_time_minutes = Column(Integer)
    difficulty = Column(String(50))  # "Fácil", "Media", "Difícil"
    region = Column(String(100))  # e.g., "Costa", "Sierra", "Selva", "Nacional"
    image_url = Column(String(500))
    tags = Column(Text)  # JSON string list
    is_local = Column(Boolean, default=True)
    nutritional_info = Column(Text)  # JSON string dict
    servings = Column(Integer, default=1)
    source_dataset = Column(String(100))
