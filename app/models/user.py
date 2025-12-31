from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from datetime import datetime, UTC
import enum
from app.db.database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime(UTC), nullable=False)
    updated_at = Column(DateTime, default=datetime(UTC), onupdate=datetime(UTC))

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"
