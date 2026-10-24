from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep the old routes and old health endpoint
app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "starter"}


# Section 11 API Contract: Health check under /api/v1
@app.get("/api/v1/health")
def health_v1():
    return {
        "status": "ok",
        "version": "v1",
        "mode": "production_foundation",
    }
