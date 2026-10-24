from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
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

# Legacy v0 routes for backwards-compatibility
app.include_router(router, prefix="/api")

# Official CONTEXT.md Section 11 API Contract routes
app.include_router(v1_router)


@app.get("/health")
def health():
    return {"status": "ok", "mode": "starter"}
