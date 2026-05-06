from fastapi import FastAPI

from app.api.routes.admin import router as admin_router
from app.api.routes.assets import router as assets_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine


Base.metadata.create_all(bind=engine)
setup_logging()

app = FastAPI(title="Custom Agents")
app.include_router(health_router)
app.include_router(jobs_router)
app.include_router(assets_router)
app.include_router(admin_router)
