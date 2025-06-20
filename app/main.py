import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Essential for serving static files (like index.html)
from fastapi.responses import FileResponse # Used for redirecting root to index.html

from app.api.routes import router as api_router # Import the main API router

# Configure basic logging for the entire application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application instance.
    This includes setting up CORS, mounting API routers, and serving static frontend files.
    """
    app = FastAPI(
        title="Data Processing & Export Microservice",
        version="1.0.0",
        description="A microservice to fetch, process, and export data to various formats, "
                    "with local and external DB support, and real-time notifications.",
        docs_url="/docs", # Default Swagger UI documentation
        redoc_url="/redoc" # Default ReDoc documentation
    )

    # Configure CORS (Cross-Origin Resource Sharing) policies.
    # This is crucial for enabling a frontend application (e.g., running on localhost:3000)
    # to make requests to this backend API (e.g., running on localhost:8000).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # WARNING: In production, replace "*" with specific trusted origins
                              # e.g., ["http://localhost:3000", "https://your-frontend-domain.com"]
        allow_credentials=True, # Allow cookies, authorization headers, etc.
        allow_methods=["*"],    # Allow all standard HTTP methods (GET, POST, PUT, DELETE, OPTIONS)
        allow_headers=["*"],    # Allow all headers in the request
    )
    logger.info("CORS middleware configured.")

    # Mount the main API router under the "/api" prefix.
    # All endpoints defined in `app.api.routes.py` and its included sub-routers
    # will now be accessible under `/api/...` (e.g., /api/config/inputs).
    app.include_router(api_router, prefix="/api")
    logger.info("API routers mounted under '/api' prefix.")

    # Mount static files to serve the frontend assets (like index.html, CSS, JavaScript, images).
    # Files in the "static" directory will be accessible at "/static/".
    # For example, "static/index.html" will be at "http://localhost:8000/static/index.html".
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Static files mounted from './static' directory under '/static'.")

    # Define a route for the root path ("/") to serve the main frontend HTML file.
    # When a user navigates to the application's root URL (e.g., http://localhost:8000/),
    # this will automatically serve the `index.html` file.
    @app.get("/", include_in_schema=False) # Exclude this internal redirect from OpenAPI docs
    async def read_root():
        """
        Redirects the root URL to the main frontend application file (index.html).
        """
        return FileResponse("static/index.html", media_type="text/html")
    logger.info("Root path '/' configured to serve 'static/index.html'.")

    return app

# Create the FastAPI application instance when the module is imported
app = create_app()
