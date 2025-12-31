from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.database import get_db
from app.schemas.costume import CostumePublic, CostumeList, CostumeFilter
from app.crud.costume import CostumeCRUD

router = APIRouter(prefix="/costumes", tags=["costumes"])
@router.get("/", response_model=List[CostumeList])
async def get_costumes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: Optional[str] = None,
    gender: Optional[str] = None,
    age_category: Optional[str] = None,
    size: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_amount: Optional[int] = Query(None, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get list of costumes (public access)."""
    # Parse tags if provided
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    # Create filter
    filters = CostumeFilter(
        name=name,
        gender=gender,
        age_category=age_category,
        size=size,
        tags=tag_list,
        min_price=min_price,
        max_price=max_price,
        min_amount=min_amount,
        is_active=True  # Only show active costumes to public
    )
    
    costumes = await CostumeCRUD.get_multi(db, skip=skip, limit=limit, filters=filters)
    
    result = []
    for costume in costumes:
        # Get first image as thumbnail with full URL
        thumbnail = None
        images_data = []
        
        if costume.images:
            # Use first image for thumbnail
            first_image = costume.images[0]
            
            # For thumbnail: return full URL
            thumbnail = first_image  # This should be the full URL
            
            # For all images: return base data for frontend processing
            for img_url in costume.images:
                # # Extract filename from URL
                # filename = img_url.split("/")[-1] if "/" in img_url else img_url
                
                # Remove extension to get base name
                base_name = img_url.rsplit('.', 1)[0]
                
                # Return base image data for frontend to construct variants
                images_data.append({
                    "base_name": base_name,
                    "original": img_url,  # Full original URL
                    "formats": ["jpg", "webp", "avif"],  # Available formats
                    "dimensions": [
                        {"suffix": "_thumb", "width": 200, "height": 200},
                        {"suffix": "_medium", "width": 800, "height": 800},
                        {"suffix": "_large", "width": 1920, "height": 1920}
                    ]
                })
        
        result.append({
            "id": costume.id,
            "name": costume.name,
            "price": costume.price,
            "gender": costume.gender.value,
            "age_category": costume.age_category.value,
            "tags": costume.tags,
            "thumbnail": thumbnail,  # Full URL to thumbnail
            "images": images_data,   # Base data for all images
            "is_active": costume.is_active
        })
    
    return result

@router.get("/search", response_model=List[CostumeList])
async def search_costumes(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Search costumes by name, description, or tags."""
    costumes = await CostumeCRUD.search(db, query=q, skip=skip, limit=limit)
    
    result = []
    for costume in costumes:
        thumbnail_url = None
        if costume.images:
            first_img = costume.images[0]
            urls = CostumeCRUD.format_for_public(costume)["images"][0]
            if "variants" in urls and "thumb" in urls["variants"]:
                thumb_variants = urls["variants"]["thumb"]
                thumbnail_url = (
                    thumb_variants.get("webp") or 
                    thumb_variants.get("avif") or 
                    thumb_variants.get("jpg")
                )
        
        result.append({
            "id": costume.id,
            "name": costume.name,
            "price": costume.price,
            "gender": costume.gender.value,
            "age_category": costume.age_category.value,
            "tags": costume.tags,
            "thumbnail": thumbnail_url,
            "is_active": costume.is_active
        })
    
    return result

@router.get("/{costume_id}", response_model=CostumePublic)
async def get_costume(
    costume_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get costume details by ID (public access)."""
    costume = await CostumeCRUD.get_by_id(db, costume_id)
    
    if not costume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Costume not found",
        )
    
    if not costume.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Costume not found",
        )
    
    return CostumeCRUD.format_for_public(costume)

@router.get("/{costume_id}/related", response_model=List[CostumeList])
async def get_related_costumes(
    costume_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get related costumes for a costume."""
    related = await CostumeCRUD.get_related_costumes(db, costume_id)
    
    result = []
    for costume in related:
        thumbnail_url = None
        if costume.images:
            first_img = costume.images[0]
            urls = CostumeCRUD.format_for_public(costume)["images"][0]
            if "variants" in urls and "thumb" in urls["variants"]:
                thumb_variants = urls["variants"]["thumb"]
                thumbnail_url = (
                    thumb_variants.get("webp") or 
                    thumb_variants.get("avif") or 
                    thumb_variants.get("jpg")
                )
        
        result.append({
            "id": costume.id,
            "name": costume.name,
            "price": costume.price,
            "gender": costume.gender.value,
            "age_category": costume.age_category.value,
            "tags": costume.tags,
            "thumbnail": thumbnail_url,
            "is_active": costume.is_active
        })
    
    return result