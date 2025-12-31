from sqlalchemy import Column, Integer, String, Float, Boolean, Text, Enum, DateTime
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from datetime import datetime, UTC
import enum
from app.db.database import Base

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"

class AgeCategory(str, enum.Enum):
    CHILD = "child"  # 3-12 лет
    TEEN = "teen"    # 13-17 лет
    ADULT = "adult"  # 18+ лет
    UNIVERSAL = "universal"

class Costume(Base):
    __tablename__ = "costumes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Inventory
    amount = Column(Integer, nullable=False, default=1)
    price = Column(Float, nullable=True)
    
    # Characteristics
    gender = Column(Enum(Gender), nullable=False, default=Gender.UNISEX)
    age_category = Column(Enum(AgeCategory), nullable=False, default=AgeCategory.UNIVERSAL)
    size = Column(String(50), nullable=True)
    tags = Column(ARRAY(String(100)), nullable=False, default=[])
    
    # Images - store as JSON
    images = Column(JSON, nullable=False, default=[])
    thumbnails = Column(ARRAY(String), nullable=False, default=[])
    
    # Related items
    items = Column(Text, nullable=True)
    related_costumes = Column(ARRAY(Integer), nullable=False, default=[])
    
    # Timestamps - use timezone-naive datetime
    created_at = Column(DateTime(timezone=False), default=datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=False), default=datetime.now(UTC), onupdate=datetime.now(UTC), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<Costume {self.name} ({self.amount} pcs)>"