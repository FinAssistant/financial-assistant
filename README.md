# AI Financial Assistant

A modern, full-stack AI-powered financial management application built with React, TypeScript, Python, and FastAPI.

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ 
- **Python** 3.11
- **UV** package manager for Python
- **Docker** (optional, for deployment)

### Setup

1. **Clone and setup the project:**
   ```bash
   git clone <repository-url>
   cd ai-financial-assistant
   ./scripts/dev-setup.sh
   ```

2. **Start development servers:**
   ```bash
   ./scripts/start-dev.sh
   ```

3. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📁 Project Structure

```
ai-financial-assistant/
├── frontend/                    # React TypeScript application
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/             # Page components
│   │   ├── store/             # Redux store configuration
│   │   ├── hooks/             # Custom React hooks
│   │   ├── utils/             # Frontend utilities
│   │   ├── types/             # TypeScript type definitions
│   │   └── styles/            # Global styles and themes
│   ├── dist/                  # Built frontend files
│   └── package.json
├── backend/                    # Python FastAPI application
│   ├── app/
│   │   ├── main.py           # FastAPI entry + static file serving
│   │   ├── core/             # Core configuration
│   │   └── static/           # Built frontend files location
│   ├── tests/                # Backend tests
│   └── pyproject.toml        # UV dependency management
├── scripts/                  # Development scripts
├── docs/                     # Project documentation
├── Dockerfile               # Production container
└── README.md
```

## 🛠️ Development

### Available Scripts

| Script | Description |
|--------|-------------|
| `./scripts/dev-setup.sh` | Initial environment setup |
| `./scripts/start-dev.sh` | Start development servers with hot reloading |
| `./scripts/build-frontend.sh` | Build frontend for production |
| `./scripts/run-tests.sh` | Run all tests (frontend + backend) |

### Development Workflow

1. **Make changes** to frontend or backend code
2. **Hot reloading** automatically updates the application
3. **Run tests** to ensure everything works
4. **Build frontend** when ready for production

### Frontend Development

- **Framework:** React 18.2.x with TypeScript 5.3.x
- **Build Tool:** Vite 5.0.x for fast development
- **Styling:** Styled Components 6.1.x with themes
- **State Management:** Redux Toolkit 1.9.x
- **Routing:** React Router DOM

```bash
cd frontend
npm run dev          # Start development server
npm run build        # Build for production
npm run test         # Run tests
npm run lint         # Lint code
```

### Backend Development

- **Framework:** FastAPI 0.104.x with Python 3.11
- **Package Management:** UV for dependency management
- **API Documentation:** Auto-generated with OpenAPI/Swagger

```bash
cd backend
source .venv/bin/activate  # Activate virtual environment
uvicorn app.main:app --reload  # Start development server
pytest                     # Run tests
```

## 🐳 Docker Deployment

### Building Docker Image

```bash
# Build production image
docker build -t ai-financial-assistant .

# Run container
docker run -p 8000:8000 ai-financial-assistant
```

## 🧪 Testing

### Run All Tests
```bash
./scripts/run-tests.sh
```

### Frontend Tests
```bash
cd frontend
npm test              # Run tests
npm run test:watch    # Watch mode
npm run test:coverage # Coverage report
```

### Backend Tests
```bash
cd backend
pytest                # Run all tests
pytest --cov         # With coverage
pytest -v            # Verbose output
```

## 🚢 Deployment

### Production Build

1. **Build frontend:**
   ```bash
   ./scripts/build-frontend.sh
   ```

2. **Build Docker image:**
   ```bash
   docker build -t ai-financial-assistant .
   ```

3. **Deploy container:**
   ```bash
   docker run -p 8000:8000 --env-file .env ai-financial-assistant
   ```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Application
APP_NAME=AI Financial Assistant
DEBUG=false
ENVIRONMENT=production

# Server
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your-production-secret-key
```

## 🏗️ Architecture

### Technology Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Frontend** | React + TypeScript | 18.2.x + 5.3.x | User interface |
| **Build Tool** | Vite | 5.0.x | Fast development |
| **Styling** | Styled Components | 6.1.x | Component styling |
| **State** | Redux Toolkit | 1.9.x | State management |
| **Backend** | FastAPI + Python | 0.104.x + 3.11.x | API server |
| **Container** | Docker | 24.x | Deployment |

### Key Features

- 🔥 **Hot Reloading** - Both frontend and backend support hot reloading
- 🎨 **Modern UI** - Styled Components with theme support
- 🔒 **Type Safety** - Full TypeScript coverage
- 📱 **Responsive** - Mobile-first design approach
- 🚀 **Fast Build** - Vite for lightning-fast development
- 🐳 **Containerized** - Docker support for consistent environments
- ✅ **Well Tested** - Comprehensive test coverage
- 📚 **Auto Docs** - API documentation generated automatically

## 🤝 Contributing

1. Follow the established code style and patterns
2. Run tests before committing: `./scripts/run-tests.sh`
3. Update documentation for new features
4. Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find and kill process using port 8000 or 5173
lsof -ti:8000 | xargs kill
lsof -ti:5173 | xargs kill
```

**Python virtual environment issues:**
```bash
cd backend
rm -rf .venv
uv venv
uv pip install -r pyproject.toml
```

**Node modules issues:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Docker issues:**
```bash
# Clean rebuild
docker build --no-cache -t ai-financial-assistant .
docker run -p 8000:8000 ai-financial-assistant
```

For more help, check the project documentation in the `docs/` directory.