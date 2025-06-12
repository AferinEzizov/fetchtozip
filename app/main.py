from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Fetch to Zip Microservice",
        version="1.0.0",
        description="A microservice to fetch, process, and export data to ZIP format",
    )

    # Optional: Set CORS policies if your frontend accesses this API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # ⚠️ Replace with specific domains in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(api_router)

    return app


app = create_app()
