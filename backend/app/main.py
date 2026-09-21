import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api import auth, products, reports, dashboard, admin, storage_api

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("visionx")

# Create database tables automatically
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-seed database if empty
    try:
        from app.database import SessionLocal
        from app.models.user import User
        db = SessionLocal()
        user_count = db.query(User).count()
        db.close()
        if user_count == 0:
            logger.info("Empty database detected. Running initial seed...")
            from seed_data.seed import run_seed
            run_seed()
    except Exception as e:
        logger.warning(f"Auto-seed check: {e}")
    yield

app = FastAPI(
    title="VisionX API",
    description="Compliance Checking System for Packaged Commodities under Legal Metrology Rules, 2011",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for seamless hackathon demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(products.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(storage_api.router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "VisionX Backend",
        "version": "1.0.0",
        "standard": "Legal Metrology (Packaged Commodities) Rules, 2011"
    }

import os
from fastapi.staticfiles import StaticFiles

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "message": "Welcome to VisionX API. Access API docs at /docs",
            "portal": "Official Government Enforcement Portal"
        }
