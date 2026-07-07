from fastapi import APIRouter
from app.api.v1.endpoints import users, auth, projects, tasks, organizations, webhooks

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
