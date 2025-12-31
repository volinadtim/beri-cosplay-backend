from fastapi import APIRouter
from app.routers import auth, users, admin, costumes
from app.routers import admin_costumes

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(admin.router)
api_router.include_router(costumes.router)  # Public costumes
api_router.include_router(admin_costumes.router)  # Admin costumes