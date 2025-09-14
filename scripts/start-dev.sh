#!/bin/bash

# AI Financial Assistant - Development Server Startup Script
# This script starts the complete solution using Docker Compose with Graphiti integration

set -e  # Exit on any error

echo "🚀 Starting AI Financial Assistant with Graphiti integration..."

# Function to cleanup docker-compose processes
cleanup() {
    echo ""
    echo "🛑 Shutting down all services..."
    docker-compose down
    echo "✅ All services stopped"
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run './scripts/dev-setup.sh' first."
    exit 1
fi

# Check if Docker and Docker Compose are available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker to run the development environment."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "🐳 Starting services with Docker Compose..."
echo "📦 Building latest development code..."

# Start all services with build
docker-compose up --build

echo ""
echo "🎉 All services are running!"
echo ""
echo "📍 Access points:"
echo "  - Frontend: http://localhost:8000 (served by FastAPI)"
echo "  - Backend API: http://localhost:8000"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo "  - MCP Server: http://localhost:8000/mcp/"
echo "  - Graphiti MCP Server: http://localhost:8080"
echo "  - Neo4j Browser: http://localhost:7474"
echo ""
echo "🔧 Development features:"
echo "  - Complete containerized environment"
echo "  - Graphiti graph database integration"
echo "  - Neo4j database with web interface"
echo "  - SQLite persistence via volume mount"
echo ""
echo "Press Ctrl+C to stop all services"