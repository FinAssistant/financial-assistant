from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import os
from pathlib import Path

from app.core.config import settings
from app.routers import auth, conversation


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files for serving built React frontend
    static_path = Path(settings.static_dir)
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # Include API routers
    app.include_router(auth.router)
    app.include_router(conversation.router)
    
    return app


app = create_app()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }


@app.get("/api/health")
async def api_health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "api": "running",
        "app": settings.app_name,
        "version": settings.app_version
    }


# Catch-all route for React app - MUST be registered last
static_path = Path(settings.static_dir)
if static_path.exists():
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve React app for client-side routing."""
        index_file = static_path / "index.html"
        if index_file.exists() and not full_path.startswith("api/"):
            with open(index_file) as f:
                return HTMLResponse(content=f.read())
        return JSONResponse({"error": "Not found"}, status_code=404)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )