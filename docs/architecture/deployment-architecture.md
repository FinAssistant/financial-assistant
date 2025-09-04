# Deployment Architecture

## Development Deployment Strategy

**Platform**: Single Docker container for simplified deployment
**Approach**: FastAPI serves both API and static React files with integrated MCP server
**Rationale**: Eliminates container orchestration complexity while maintaining production patterns

### MCP Server Integration
- **POC Approach**: MCP server mounted within FastAPI at `/mcp` endpoint for simplified single-container deployment
- **Lifecycle Management**: Combined lifespan management ensures FastAPI and MCP server start/stop together  
- **Future Flexibility**: `run_server()` function enables independent MCP server deployment when needed

### Data Persistence
- **SQLite Database**: Persistent local file storage (`./financial_assistant.db`)
- **Container Volumes**: Database file persisted via Docker volume mounts
- **Backup Strategy**: Database file can be copied for backup/restore operations

### Single Container Deployment

```dockerfile
# Multi-stage build for production
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS backend
WORKDIR /app

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy backend code
COPY backend/ ./

# Install dependencies with UV
RUN uv sync --frozen

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./app/static

# Create database directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Start application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Environment Strategy

| Environment | Frontend URL | Backend URL | Purpose |
|-------------|--------------|-------------|---------|
| Development | http://localhost:5173 | http://localhost:8000 | Local development |
| Staging | TBD | TBD | Pre-production testing |
| Production | TBD | TBD | Live POC environment |