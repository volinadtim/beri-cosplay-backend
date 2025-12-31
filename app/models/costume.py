from sqlalchemy import Column, DateTime, Integer, String, Float, Boolean, Text, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
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
    price = Column(Float, nullable=True)  # Price per day in RUB
    
    # Characteristics
    gender = Column(Enum(Gender), nullable=False, default=Gender.UNISEX)
    age_category = Column(Enum(AgeCategory), nullable=False, default=AgeCategory.UNIVERSAL)
    size = Column(String(50), nullable=True)  # S, M, L, XL or specific measurements
    tags = Column(ARRAY(String(100)), nullable=False, default=[])  # ["Принцесса", "Русалочка", "Сказка"]
    
    # Related items (comma-separated or JSON)
    items = Column(Text, nullable=True)  # Additional items: "корона, жезл, туфли"
    
    # Images - stored as JSON with hash and variants
    images = Column(JSON, nullable=False, default=[])
    
    # Relations
    related_costumes = Column(ARRAY(Integer), nullable=False, default=[])  # IDs of related costumes
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<Costume {self.name} ({self.amount} pcs)>"