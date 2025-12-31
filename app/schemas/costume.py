from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from app.models.costume import Gender, AgeCategory

# Enums for schemas
class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"

class AgeCategoryEnum(str, Enum):
    CHILD = "child"
    TEEN = "teen"
    ADULT = "adult"
    UNIVERSAL = "universal"

# Image schemas
class ImageVariant(BaseModel):
    format: str
    width: int
    height: int
    quality: int
    path: str
    size: int
    suffix: str
    
    class Config:
        from_attributes = True

class ImageInfo(BaseModel):
    original_name: str
    hash: str
    original_path: str
    variants: List[ImageVariant]
    total_size: int
    
    class Config:
        from_attributes = True

# Base costume schemas
class CostumeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    amount: int = Field(1, ge=0)
    price: Optional[float] = Field(None, ge=0)
    gender: GenderEnum = GenderEnum.UNISEX
    age_category: AgeCategoryEnum = AgeCategoryEnum.UNIVERSAL
    size: Optional[str] = Field(None, max_length=50)
    tags: List[str] = Field(default_factory=list)
    items: Optional[str] = Field(None, max_length=500)
    related_costumes: List[int] = Field(default_factory=list)
    
    @field_validator('tags')
    def validate_tags(cls, v):
        if len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        if any(len(tag) > 100 for tag in v):
            raise ValueError('Tag cannot exceed 100 characters')
        return v
    
    @field_validator('related_costumes')
    def validate_related_costumes(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 related costumes allowed')
        return v

class CostumeCreate(CostumeBase):
    pass

class CostumeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    amount: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, ge=0)
    gender: Optional[GenderEnum] = None
    age_category: Optional[AgeCategoryEnum] = None
    size: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    items: Optional[str] = Field(None, max_length=500)
    related_costumes: Optional[List[int]] = None
    is_active: Optional[bool] = None
    
    @field_validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 20:
                raise ValueError('Maximum 20 tags allowed')
            if any(len(tag) > 100 for tag in v):
                raise ValueError('Tag cannot exceed 100 characters')
        return v
    
    @field_validator('related_costumes')
    def validate_related_costumes(cls, v):
        if v is not None and len(v) > 10:
            raise ValueError('Maximum 10 related costumes allowed')
        return v

# Response schemas
class CostumeInDB(CostumeBase):
    id: int
    images: List[ImageInfo] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class CostumeResponse(CostumeInDB):
    pass

class CostumePublic(BaseModel):
    """Public view of costume (without sensitive info)"""
    id: int
    name: str
    description: Optional[str]
    price: Optional[float]
    gender: GenderEnum
    age_category: AgeCategoryEnum
    size: Optional[str]
    tags: List[str]
    items: Optional[str]
    images: List[Dict[str, Any]]  # Only public image info
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

# For listing
class CostumeList(BaseModel):
    id: int
    name: str
    price: Optional[float]
    gender: GenderEnum
    age_category: AgeCategoryEnum
    tags: List[str]
    thumbnail: Optional[str]  # URL to thumbnail
    is_active: bool
    
    class Config:
        from_attributes = True

# Query filters
class CostumeFilter(BaseModel):
    name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    age_category: Optional[AgeCategoryEnum] = None
    size: Optional[str] = None
    tags: Optional[List[str]] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_amount: Optional[int] = None
    is_active: Optional[bool] = True
    
    class Config:
        extra = "forbid"