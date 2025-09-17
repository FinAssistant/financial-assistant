from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pathlib import Path
import logging

from app.core.config import settings
from app.routers import auth, conversation

logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Application-specific startup and shutdown logic."""
    # Startup
    logger.info("Starting up FastAPI application...")
    
    # Initialize AsyncSqliteSaver checkpointer
    from app.ai.orchestrator_agent import setup_checkpointer
    await setup_checkpointer()
    
    # Initialize Graphiti MCP tools for all agents
    from app.ai.mcp_clients.graphiti_client import setup_graphiti_tools
    await setup_graphiti_tools()
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    from app.ai.orchestrator_agent import cleanup_checkpointer
    await cleanup_checkpointer()



def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    # Get FastMCP http app
    from mcp_server.server import get_mcp_app
    mcp_app = get_mcp_app()


    @asynccontextmanager 
    async def combined_lifespan(app: FastAPI):
        """Combined lifespan manager for FastAPI and MCP server."""
        # Run FastAPI lifespan
        async with app_lifespan(app):
            async with mcp_app.lifespan(app):
                logger.info("FastMCP server integrated with FastAPI via combined lifespan")
                yield
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=combined_lifespan,  # Use combined lifespan context manager
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
    
    # Mount FastMCP server at /mcp
    try:
        app.mount("/mcp", mcp_app)
        logger.info("FastMCP server mounted at /mcp/")
    except Exception as e:
        logger.error(f"Failed to mount FastMCP server: {str(e)}")
        logger.warning("Continuing without MCP server")
    
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
    # Check if MCP server is mounted by looking for /mcp route
    mcp_mounted = False
    try:
        from starlette.routing import Mount
        for route in app.routes:
            if isinstance(route, Mount) and route.path == "/mcp":
                mcp_mounted = True
                break
    except:
        pass
    
    return {
        "status": "healthy",
        "api": "running",
        "app": settings.app_name,
        "version": settings.app_version,
        "mcp_server": {
            "status": "integrated" if mcp_mounted else "not_mounted",
            "mount_point": "/mcp/" if mcp_mounted else None,
            "server": "FastMCP",
            "pattern": "combined_lifespan"
        }
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