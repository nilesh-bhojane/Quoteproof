from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.v1.quotes import router as quotes_v1_router
from app.api.v1.products import router as products_v1_router
from app.api.v1_routes import v1_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep legacy routes and starter health endpoint for backward compatibility
app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "starter"}


# Section 11 API Contract: Health check and Part 1 endpoints under /api/v1
@app.get("/api/v1/health")
def health_v1():
    return {
        "status": "ok",
        "version": "v1",
        "mode": "production_foundation",
    }


# Include modular v1 routers (Part 1 - Quotes & Products)
app.include_router(quotes_v1_router, prefix="/api/v1")
app.include_router(products_v1_router, prefix="/api/v1")

# Include remaining Section 11 API Contract routes (Part 2 & 3: Timings, ROI, Audit, Settings, Trust Test, etc.)
app.include_router(v1_router)
