#!/bin/bash

# AI Financial Assistant - Development Setup Script
# This script sets up the development environment for both frontend and backend

set -e  # Exit on any error

echo "🚀 Setting up AI Financial Assistant development environment..."

# Check if required tools are installed
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed. Please install it first."
        exit 1
    fi
}

echo "📋 Checking required tools..."
check_tool "node"
check_tool "npm"
check_tool "python3"
check_tool "uv"

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18 or higher is required. Current version: $(node --version)"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
if [ "$PYTHON_VERSION" != "3.11" ]; then
    echo "⚠️  Python 3.11 is recommended. Current version: $(python3 --version)"
fi

echo "✅ All required tools are available"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please update it with your configuration."
else
    echo "✅ .env file already exists"
fi

# Install backend dependencies
echo "🐍 Installing backend dependencies..."
cd backend
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    uv venv
fi

echo "Installing Python packages..."
uv pip install -r pyproject.toml

cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend

if [ -f "package-lock.json" ]; then
    npm ci
else
    npm install
fi

cd ..

echo "🎉 Development environment setup complete!"
echo ""
echo "🔧 Next steps:"
echo "  1. Update your .env file with the required configuration"
echo "  2. Run './scripts/start-dev.sh' to start the development servers"
echo "  3. Access the application at http://localhost:5173 (frontend), http://localhost:8000 (backend), or http://localhost:8080 (Graphiti MCP)"
echo ""
echo "📚 Available scripts:"
echo "  - ./scripts/start-dev.sh        - Start development servers"
echo "  - ./scripts/build-frontend.sh   - Build frontend for production"
echo "  - ./scripts/run-tests.sh        - Run all tests"