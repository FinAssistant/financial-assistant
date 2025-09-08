#!/bin/bash

# AI Financial Assistant - Frontend Build Script
# This script builds the frontend and copies it to the backend static directory

set -e  # Exit on any error

echo "🏗️  Building frontend for production..."

# Check if dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies not installed. Please run './scripts/dev-setup.sh' first."
    exit 1
fi

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf backend/app/static/*

# Build frontend
echo "📦 Building React application..."
cd frontend

# Run TypeScript compiler
echo "🔍 Type checking..."
npm run build

cd ..

# Verify build output
if [ ! -d "backend/app/static" ] || [ -z "$(ls -A backend/app/static)" ]; then
    echo "❌ Build failed - no output in backend/app/static"
    exit 1
fi

echo "✅ Frontend build completed successfully!"
echo ""
echo "📂 Build output location: backend/app/static/"
echo "📊 Build size:"
du -sh backend/app/static/*

echo ""
echo "🚀 Ready for deployment! You can now:"
echo "  1. Start the backend server to serve the built frontend"
echo "  2. Build and run the Docker container"
echo "  3. Deploy to your production environment"