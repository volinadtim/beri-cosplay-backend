from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_, and_
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status, UploadFile
from typing import List, Optional, Dict, Any
import json

from app.models.costume import Costume, Gender, AgeCategory
from app.schemas.costume import CostumeCreate, CostumeUpdate, CostumeFilter, ImageInfo
from app.core.images import image_processor
from app.models.user import UserRole

class CostumeCRUD:
    @staticmethod
    async def get_by_id(db: AsyncSession, costume_id: int) -> Optional[Costume]:
        """Get costume by ID."""
        result = await db.execute(
            select(Costume).where(Costume.id == costume_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_multi(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[CostumeFilter] = None
    ) -> List[Costume]:
        """Get multiple costumes with optional filters."""
        query = select(Costume)
        
        if filters:
            # Apply filters
            conditions = []
            
            if filters.name:
                conditions.append(Costume.name.ilike(f"%{filters.name}%"))
            
            if filters.gender:
                conditions.append(Costume.gender == filters.gender)
            
            if filters.age_category:
                conditions.append(Costume.age_category == filters.age_category)
            
            if filters.size:
                conditions.append(Costume.size == filters.size)
            
            if filters.tags:
                # Find costumes that have ALL specified tags
                for tag in filters.tags:
                    conditions.append(Costume.tags.contains([tag]))
            
            if filters.min_price is not None:
                conditions.append(Costume.price >= filters.min_price)
            
            if filters.max_price is not None:
                conditions.append(Costume.price <= filters.max_price)
            
            if filters.min_amount is not None:
                conditions.append(Costume.amount >= filters.min_amount)
            
            if filters.is_active is not None:
                conditions.append(Costume.is_active == filters.is_active)
            
            if conditions:
                query = query.where(and_(*conditions))
        
        query = query.order_by(Costume.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def create(
        db: AsyncSession, 
        costume_data: CostumeCreate,
        images: Optional[List[UploadFile]] = None
    ) -> Costume:
        """Create a new costume."""
        # Check if costume with same name exists
        existing = await db.execute(
            select(Costume).where(Costume.name == costume_data.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Costume with this name already exists",
            )
        
        # Process images if provided
        processed_images = []
        if images:
            for image in images:
                if image.content_type not in ['image/jpeg', 'image/png', 'image/webp', 'image/avif']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid image type: {image.content_type}"
                    )
                
                if image.size > 10 * 1024 * 1024:  # 10MB limit
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Image too large (max 10MB)"
                    )
                
                try:
                    image_info = await image_processor.process_image(image)
                    processed_images.append(image_info)
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to process image: {str(e)}"
                    )
        
        # Create costume
        db_costume = Costume(
            **costume_data.model_dump(),
            images=processed_images
        )
        
        db.add(db_costume)
        try:
            await db.commit()
            await db.refresh(db_costume)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create costume",
            )
        
        return db_costume
    
    @staticmethod
    async def update(
        db: AsyncSession,
        costume_id: int,
        costume_data: CostumeUpdate,
        add_images: Optional[List[UploadFile]] = None,
        remove_image_hashes: Optional[List[str]] = None
    ) -> Costume:
        """Update a costume."""
        costume = await CostumeCRUD.get_by_id(db, costume_id)
        if not costume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Costume not found",
            )
        
        # Update basic fields
        update_data = costume_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(costume, field, value)
        
        # Remove images if requested
        if remove_image_hashes:
            images_to_keep = []
            for img in costume.images:
                if img['hash'] not in remove_image_hashes:
                    images_to_keep.append(img)
                else:
                    # Delete image files
                    await image_processor.delete_image(img['hash'])
            costume.images = images_to_keep
        
        # Add new images
        if add_images:
            for image in add_images:
                if image.content_type not in ['image/jpeg', 'image/png', 'image/webp', 'image/avif']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid image type: {image.content_type}"
                    )
                
                if image.size > 10 * 1024 * 1024:  # 10MB limit
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Image too large (max 10MB)"
                    )
                
                try:
                    image_info = await image_processor.process_image(image)
                    costume.images.append(image_info)
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to process image: {str(e)}"
                    )
        
        try:
            await db.commit()
            await db.refresh(costume)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update costume",
            )
        
        return costume
    
    @staticmethod
    async def delete(db: AsyncSession, costume_id: int) -> bool:
        """Delete a costume."""
        costume = await CostumeCRUD.get_by_id(db, costume_id)
        if not costume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Costume not found",
            )
        
        # Delete associated images
        for img in costume.images:
            await image_processor.delete_image(img['hash'])
        
        await db.delete(costume)
        await db.commit()
        return True
    
    @staticmethod
    async def search(
        db: AsyncSession,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Costume]:
        """Search costumes by name, description, or tags."""
        search_query = select(Costume).where(
            or_(
                Costume.name.ilike(f"%{query}%"),
                Costume.description.ilike(f"%{query}%"),
                Costume.items.ilike(f"%{query}%")
            )
        ).where(Costume.is_active == True).offset(skip).limit(limit)
        
        result = await db.execute(search_query)
        return result.scalars().all()
    
    @staticmethod
    async def get_related_costumes(
        db: AsyncSession,
        costume_id: int
    ) -> List[Costume]:
        """Get costumes related to the specified costume."""
        costume = await CostumeCRUD.get_by_id(db, costume_id)
        if not costume:
            return []
        
        if not costume.related_costumes:
            return []
        
        result = await db.execute(
            select(Costume).where(
                Costume.id.in_(costume.related_costumes),
                Costume.is_active == True
            )
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_amount(
        db: AsyncSession,
        costume_id: int,
        delta: int  # Positive to add, negative to subtract
    ) -> Costume:
        """Update costume amount (for inventory management)."""
        costume = await CostumeCRUD.get_by_id(db, costume_id)
        if not costume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Costume not found",
            )
        
        new_amount = costume.amount + delta
        if new_amount < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reduce amount below zero",
            )
        
        costume.amount = new_amount
        await db.commit()
        await db.refresh(costume)
        return costume
    
    @staticmethod
    def format_for_public(costume: Costume) -> Dict[str, Any]:
        """Format costume data for public view."""
        # Generate image URLs for public
        image_urls = []
        for img in costume.images:
            urls = image_processor.get_image_urls(img['hash'], img['original_name'])
            image_urls.append(urls)
        
        return {
            "id": costume.id,
            "name": costume.name,
            "description": costume.description,
            "price": costume.price,
            "gender": costume.gender.value,
            "age_category": costume.age_category.value,
            "size": costume.size,
            "tags": costume.tags,
            "items": costume.items,
            "images": image_urls,
            "created_at": costume.created_at,
            "is_active": costume.is_active
        }