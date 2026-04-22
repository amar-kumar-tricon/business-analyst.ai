"""
app.api.v1.router
=================
Aggregates all v1 resource routers into a single `api_router` mounted at `/api`.

To add a new resource:
    1. create `app/api/v1/<resource>.py` exposing `router = APIRouter(...)`
    2. import and `api_router.include_router(<resource>.router)` below
"""
from fastapi import APIRouter

from app.api.v1 import (
    analyse,
    architecture,
    discovery,
    documents,
    export,
    projects,
    settings as settings_routes,
    sprint,
    versions,
)

api_router = APIRouter()
api_router.include_router(projects.router)
api_router.include_router(documents.router)
api_router.include_router(analyse.router)
api_router.include_router(discovery.router)
api_router.include_router(architecture.router)
api_router.include_router(sprint.router)
api_router.include_router(versions.router)
api_router.include_router(export.router)
api_router.include_router(settings_routes.router)
