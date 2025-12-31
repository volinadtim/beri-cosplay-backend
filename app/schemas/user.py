from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole

# Base schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    full_name: Optional[str] = Field(None, max_length=100)

# Create schemas
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: Optional[UserRole] = UserRole.USER
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserCreateAdmin(UserCreate):
    role: UserRole = UserRole.USER  # Admins can only create regular users by default

# Update schemas
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    
    @validator('password')
    def validate_password(cls, v):
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class AdminUserUpdate(UserUpdate):
    role: Optional[UserRole] = None
    is_verified: Optional[bool] = None

# Response schemas
class UserInDB(UserBase):
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserResponse(UserInDB):
    pass

class UserWithToken(UserResponse):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Login schemas
class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str
    
    @validator('email', 'username')
    def validate_identifier(cls, v, values, field):
        if field.name == 'email' and v is None and values.get('username') is None:
            raise ValueError('Either email or username must be provided')
        if field.name == 'username' and v is None and values.get('email') is None:
            raise ValueError('Either email or username must be provided')
        return v

class LoginResponse(Token):
    user: UserResponse