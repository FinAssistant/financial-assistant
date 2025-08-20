# Technical Assumptions

## Repository Structure

**Monorepo** - Single repository with clear separation between frontend and backend components

## Service Architecture

**Monolith** - Self-hosted solution with Python backend serving React frontend files

## Testing Requirements

**Unit + Integration** - Focus on core functionality testing without over-engineering for POC

## Additional Technical Assumptions

**Platform & Infrastructure:**

*   **Deployment**: Self-hosted solution (Docker-friendly for easy deployment)
    
*   **No vendor lock-in**: Avoid serverless provider dependencies
    

**Technology Stack:**

*   **Frontend**: React (served by backend)
    
*   **Backend**: Python with FastAPI (recommended over alternatives for API docs, async support, and Python ecosystem compatibility)
    
*   **AI Framework**: LangGraph with configurable LLM providers via .env
    
*   **Data Storage**: In-memory storage for POC (no database setup required)
    
*   **Authentication**: Google OAuth for user authentication
    

**Configuration & Environment:**

*   **AI Provider**: Configurable via environment variables (OpenAI, Claude, etc.)
    
*   **Secrets Management**: .env file for development, proper secrets management for production
    
*   **Build Process**: Simple build pipeline that bundles React and serves via Python backend
    

**Development Approach:**

*   Focus on core user flow validation
    
*   Minimal viable feature set for POC
    
*   Easy local development setup