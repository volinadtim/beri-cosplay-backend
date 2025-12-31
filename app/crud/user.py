from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, AdminUserUpdate
from app.core.security import get_password_hash, verify_password
from typing import List, Optional

class UserCRUD:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def authenticate(db: AsyncSession, identifier: str, password: str) -> Optional[User]:
        """Authenticate user by email/username and password."""
        # Try email first
        user = await UserCRUD.get_by_email(db, identifier)
        if not user:
            # Try username
            user = await UserCRUD.get_by_username(db, identifier)
        
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        
        return user

    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate) -> User:
        """Create new user."""
        # Check if user exists
        if await UserCRUD.get_by_email(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        if await UserCRUD.get_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=user_data.role,
        )
        
        db.add(db_user)
        try:
            await db.commit()
            await db.refresh(db_user)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User creation failed",
            )
        
        return db_user

    @staticmethod
    async def update(
        db: AsyncSession, 
        user_id: int, 
        user_data: UserUpdate,
        current_user: User
    ) -> User:
        """Update user (regular users can only update themselves)."""
        if current_user.id != user_id and current_user.role == UserRole.USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update other users",
            )
        
        user = await UserCRUD.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        try:
            await db.commit()
            await db.refresh(user)
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Update failed",
            )
        
        return user

    @staticmethod
    async def admin_update(
        db: AsyncSession,
        user_id: int,
        user_data: AdminUserUpdate
    ) -> User:
        """Admin update user with all fields."""
        user = await UserCRUD.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        update_data = user_data.dict(exclude_unset=True)
        
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        try:
            await db.commit()
            await db.refresh(user)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Update failed",
            )
        
        return user

    @staticmethod
    async def delete(db: AsyncSession, user_id: int, current_user: User) -> bool:
        """Delete user."""
        if current_user.id != user_id and current_user.role == UserRole.USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete other users",
            )
        
        user = await UserCRUD.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()
        return True

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> List[User]:
        """Get all users with pagination."""
        query = select(User)
        
        if active_only:
            query = query.where(User.is_active == True)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search(
        db: AsyncSession,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[User]:
        """Search users by email, username, or full name."""
        search_query = select(User).where(
            (User.email.ilike(f"%{query}%")) |
            (User.username.ilike(f"%{query}%")) |
            (User.full_name.ilike(f"%{query}%"))
        ).offset(skip).limit(limit)
        
        result = await db.execute(search_query)
        return result.scalars().all()

    @staticmethod
    async def change_role(
        db: AsyncSession,
        user_id: int,
        role: UserRole,
        admin_user: User
    ) -> User:
        """Change user role (admin only)."""
        if admin_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        
        user = await UserCRUD.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Super admin cannot be demoted by admin
        if user.role == UserRole.SUPER_ADMIN and admin_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify super admin",
            )
        
        user.role = role
        await db.commit()
        await db.refresh(user)
        return user