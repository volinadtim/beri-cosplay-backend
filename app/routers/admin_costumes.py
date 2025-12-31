from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
from app.db.database import get_db
from app.schemas.costume import CostumeCreate, CostumeUpdate, CostumeResponse
from app.crud.costume import CostumeCRUD
from app.dependencies.auth import get_current_admin
from app.models.user import User

router = APIRouter(prefix="/admin/costumes", tags=["admin-costumes"])


@router.get("/", response_model=List[CostumeResponse])
async def admin_get_costumes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Get all costumes (admin only, includes inactive)."""
    filters = None
    if is_active is not None:
        from app.schemas.costume import CostumeFilter

        filters = CostumeFilter(is_active=is_active)

    costumes = await CostumeCRUD.get_multi(db, skip=skip, limit=limit, filters=filters)
    return costumes


@router.get("/{costume_id}", response_model=CostumeResponse)
async def admin_get_costume(
    costume_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_admin)
):
    """Get costume by ID (admin only)."""
    costume = await CostumeCRUD.get_by_id(db, costume_id)
    if not costume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Costume not found",
        )
    return costume


@router.post("/", response_model=CostumeResponse, status_code=status.HTTP_201_CREATED)
async def create_costume(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    amount: int = Form(1),
    price: Optional[float] = Form(None),
    gender: str = Form("unisex"),
    age_category: str = Form("universal"),
    size: Optional[str] = Form(None),
    tags: str = Form("[]"),  # Accept as string, will parse as JSON
    items: Optional[str] = Form(None),
    related_costumes: str = Form("[]"),  # Accept as string, will parse as JSON
    images: Optional[List[UploadFile]] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Create a new costume."""
    try:
        # Parse tags - handle both JSON array and comma-separated string
        tags_list = []
        if tags and tags.strip():
            try:
                # Try to parse as JSON first
                tags_list = json.loads(tags)
                if not isinstance(tags_list, list):
                    tags_list = [tags_list]
            except json.JSONDecodeError:
                # If not JSON, treat as comma-separated string
                tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Parse related costumes
        related_list = []
        if related_costumes and related_costumes.strip():
            try:
                related_list = json.loads(related_costumes)
                if not isinstance(related_list, list):
                    related_list = [int(related_list)] if related_list else []
            except (json.JSONDecodeError, ValueError):
                # If not JSON, treat as comma-separated IDs
                related_list = []
                for item in related_costumes.split(","):
                    if item.strip():
                        try:
                            related_list.append(int(item.strip()))
                        except ValueError:
                            pass

        # Handle price - convert empty string to None
        price_value = float(price) if price and str(price).strip() else None

        # Create costume data
        costume_data = CostumeCreate(
            name=name,
            description=description if description and description.strip() else None,
            amount=amount,
            price=price_value,
            gender=gender,
            age_category=age_category,
            size=size if size and size.strip() else None,
            tags=tags_list,
            items=items if items and items.strip() else None,
            related_costumes=related_list,
        )

        # Create costume
        costume = await CostumeCRUD.create(db, costume_data, images)
        return costume

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create costume: {str(e)}")


@router.put("/{costume_id}", response_model=CostumeResponse)
async def update_costume(
    costume_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    amount: Optional[int] = Form(None),
    price: Optional[float] = Form(None),
    gender: Optional[str] = Form(None),
    age_category: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    items: Optional[str] = Form(None),
    related_costumes: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Update a costume."""
    try:
        update_data = {}

        # Handle optional fields
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description if description.strip() else None
        if amount is not None:
            update_data["amount"] = amount
        if price is not None:
            update_data["price"] = float(price) if str(price).strip() else None
        if gender is not None:
            update_data["gender"] = gender
        if age_category is not None:
            update_data["age_category"] = age_category
        if size is not None:
            update_data["size"] = size if size.strip() else None
        if items is not None:
            update_data["items"] = items if items.strip() else None
        if is_active is not None:
            update_data["is_active"] = is_active

        # Parse tags if provided
        if tags is not None:
            tags_list = []
            if tags.strip():
                try:
                    tags_list = json.loads(tags)
                    if not isinstance(tags_list, list):
                        tags_list = [tags_list]
                except json.JSONDecodeError:
                    tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            update_data["tags"] = tags_list

        # Parse related costumes if provided
        if related_costumes is not None:
            related_list = []
            if related_costumes.strip():
                try:
                    related_list = json.loads(related_costumes)
                    if not isinstance(related_list, list):
                        related_list = [int(related_list)] if related_list else []
                except (json.JSONDecodeError, ValueError):
                    related_list = []
                    for item in related_costumes.split(","):
                        if item.strip():
                            try:
                                related_list.append(int(item.strip()))
                            except ValueError:
                                pass
            update_data["related_costumes"] = related_list

        # Update costume
        costume_update = CostumeUpdate(**update_data)
        costume = await CostumeCRUD.update(db, costume_id, costume_update)

        return costume

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to update costume: {str(e)}")


@router.delete("/{costume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_costume(
    costume_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_admin)
):
    """Delete a costume (admin only)."""
    await CostumeCRUD.delete(db, costume_id)
    return None


@router.post("/{costume_id}/amount", response_model=CostumeResponse)
async def update_costume_amount(
    costume_id: int,
    delta: int = Form(..., description="Positive to add, negative to subtract"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Update costume amount (inventory management)."""
    costume = await CostumeCRUD.update_amount(db, costume_id, delta)
    return costume


@router.get("/search/all", response_model=List[CostumeResponse])
async def admin_search_costumes(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Search all costumes (admin only)."""
    costumes = await CostumeCRUD.search(db, query=q, skip=skip, limit=limit)
    return costumes
