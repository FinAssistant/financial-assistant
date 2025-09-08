# Development Workflow

## Local Development Setup

### Prerequisites
```bash
# Install required tools
node -v    # v18+ required
python -v  # 3.11+ required
uv --version  # Latest UV package manager
```

### Initial Setup
```bash
# Clone and setup project
git clone <repository-url>
cd ai-financial-assistant

# Backend setup with UV
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync  # Install dependencies from pyproject.toml

# Frontend setup
cd ../frontend
npm install

# Environment configuration
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Development Commands (Simplified)
```bash
# Option 1: Start all services with script
./scripts/start-dev.sh

# Option 2: Start manually in separate terminals

# Terminal 1: Backend development server
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend development server (proxies to backend)
cd frontend
npm run dev

# Build and serve from single server (production-like)
./scripts/build-frontend.sh  # Builds frontend to backend/app/static/
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Now serves both API and frontend from port 8000
```

## Environment Configuration

### Required Environment Variables
```bash
# Frontend (.env.local)
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your_google_oauth_client_id
VITE_PLAID_ENV=sandbox

# Backend (.env)
# AI Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_claude_api_key  
AI_PROVIDER=openai  # or anthropic

# Authentication
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_secret
JWT_SECRET_KEY=your_jwt_secret_key

# Plaid Configuration
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret_key
PLAID_ENV=sandbox

# Application
DEBUG=true
LOG_LEVEL=info
CORS_ORIGINS=http://localhost:5173
```

## FastAPI Main Application with Static File Serving

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(title="AI Financial Assistant API")

# Include API routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(conversation_router, prefix="/api/conversation", tags=["conversation"])
app.include_router(plaid_router, prefix="/api/plaid", tags=["plaid"])
app.include_router(accounts_router, prefix="/api/accounts", tags=["accounts"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["analysis"])

# Serve static files (built React app)
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve React app for all non-API routes"""
        # If it's an API route, let it pass through
        if full_path.startswith("api/"):
            return {"error": "API endpoint not found"}
        
        # For all other routes, serve the React app
        index_path = os.path.join(static_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        return {"error": "Frontend not built. Run build-frontend.sh first."}

@app.get("/")
async def root():
    """Serve React app from root"""
    return await serve_react_app("")
```

## UV Dependency Management

### Backend pyproject.toml
```toml
[project]
name = "ai-financial-assistant"
version = "0.1.0"
description = "AI-powered financial assistant POC"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    "python-jose[cryptography]>=3.3.0",
    "python-multipart>=0.0.6",
    "plaid-python>=9.0.0",
    "langgraph>=0.0.40",
    "openai>=1.0.0",
    "anthropic>=0.7.0",
    "cryptography>=41.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.6.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.6.0",
]
```

## Build and Deployment Scripts

### scripts/build-frontend.sh
```bash
#!/bin/bash
set -e

echo "Building frontend..."
cd frontend
npm run build

echo "Copying built files to backend static directory..."
rm -rf ../backend/app/static
cp -r dist ../backend/app/static

echo "Frontend built and copied successfully!"
echo "You can now run the backend server to serve both API and frontend"
```

### scripts/start-dev.sh
```bash
#!/bin/bash

# Start backend in background
echo "Starting backend server..."
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend dev server
echo "Starting frontend dev server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Wait for Ctrl+C
echo "Both servers running. Press Ctrl+C to stop."
wait

# Cleanup
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
```