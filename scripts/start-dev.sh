#!/bin/bash

# AI Financial Assistant - Development Server Startup Script
# This script starts both frontend and backend development servers

set -e  # Exit on any error

echo "🚀 Starting AI Financial Assistant development servers..."

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $1 is already in use"
        return 1
    fi
    return 0
}

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down development servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "✅ Backend server stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "✅ Frontend server stopped"
    fi
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run './scripts/dev-setup.sh' first."
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "backend/.venv" ]; then
    echo "❌ Backend dependencies not installed. Please run './scripts/dev-setup.sh' first."
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies not installed. Please run './scripts/dev-setup.sh' first."
    exit 1
fi

# Check ports
echo "🔍 Checking available ports..."
if ! check_port 8000; then
    echo "❌ Backend port 8000 is in use. Please stop the service using this port."
    exit 1
fi

if ! check_port 5173; then
    echo "❌ Frontend port 5173 is in use. Please stop the service using this port."
    exit 1
fi

echo "✅ Ports 8000 and 5173 are available"

# Start backend server
echo "🐍 Starting backend server on http://localhost:8000..."
cd backend
source .venv/bin/activate 2>/dev/null || true
export DEBUG=true
export ENVIRONMENT=development
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start frontend server
echo "⚛️  Starting frontend server on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "🎉 Development servers are starting up!"
echo ""
echo "📍 Access points:"
echo "  - Frontend: http://localhost:5173"
echo "  - Backend API: http://localhost:8000"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo ""
echo "🔧 Development features:"
echo "  - Hot reloading enabled for both frontend and backend"
echo "  - Frontend proxy configured to route API calls to backend"
echo "  - Source maps enabled for debugging"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait