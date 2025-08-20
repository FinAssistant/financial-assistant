#!/bin/bash

# AI Financial Assistant - Test Runner Script
# This script runs all tests for both frontend and backend

set -e  # Exit on any error

echo "🧪 Running AI Financial Assistant test suite..."

# Function to check if dependencies are installed
check_dependencies() {
    if [ ! -d "backend/.venv" ]; then
        echo "❌ Backend dependencies not installed. Please run './scripts/dev-setup.sh' first."
        exit 1
    fi

    if [ ! -d "frontend/node_modules" ]; then
        echo "❌ Frontend dependencies not installed. Please run './scripts/dev-setup.sh' first."
        exit 1
    fi
}

# Function to run backend tests
run_backend_tests() {
    echo "🐍 Running backend tests..."
    cd backend
    
    # Activate virtual environment
    source .venv/bin/activate 2>/dev/null || true
    
    # Run tests with coverage
    echo "Running pytest with coverage..."
    python -m pytest --cov=app --cov-report=term-missing --cov-report=html:htmlcov tests/
    
    echo "✅ Backend tests completed"
    cd ..
}

# Function to run frontend tests
run_frontend_tests() {
    echo "⚛️  Running frontend tests..."
    cd frontend
    
    # Run tests with coverage
    echo "Running Jest with coverage..."
    npm run test:coverage -- --watchAll=false
    
    echo "✅ Frontend tests completed"
    cd ..
}

# Function to display test results summary
show_summary() {
    echo ""
    echo "📊 Test Results Summary"
    echo "======================"
    
    if [ -f "backend/htmlcov/index.html" ]; then
        echo "🐍 Backend coverage report: backend/htmlcov/index.html"
    fi
    
    if [ -f "frontend/coverage/lcov-report/index.html" ]; then
        echo "⚛️  Frontend coverage report: frontend/coverage/lcov-report/index.html"
    fi
    
    echo ""
    echo "🎉 All tests completed successfully!"
}

# Main execution
echo "🔍 Checking dependencies..."
check_dependencies

echo "✅ Dependencies check passed"
echo ""

# Run tests
run_backend_tests
echo ""
run_frontend_tests
echo ""

# Show summary
show_summary

echo ""
echo "💡 Tips:"
echo "  - Run 'cd backend && pytest --cov=app tests/' for backend tests only"
echo "  - Run 'cd frontend && npm test' for frontend tests only"
echo "  - Run 'cd frontend && npm run test:watch' for frontend watch mode"