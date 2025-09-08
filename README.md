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
   - Graphiti MCP Server: http://localhost:8080

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

# MCP Server Configuration
MCP_SERVER_NAME=financial-assistant-mcp
MCP_SERVER_VERSION=0.1.0
MCP_SERVER_PORT=8001
MCP_LOG_LEVEL=INFO

# Plaid Configuration (Optional - for financial data access)
PLAID_CLIENT_ID=your-plaid-client-id
PLAID_SECRET=your-plaid-secret
PLAID_ENV=sandbox
PLAID_PRODUCTS=["transactions", "accounts", "balances"]
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
# Find and kill process using port 8000, 8080, or 5173
lsof -ti:8000 | xargs kill
lsof -ti:8080 | xargs kill  
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

## 🏦 Plaid Integration Setup

The application includes Plaid API integration through the MCP (Model Context Protocol) server for accessing financial data.

### Plaid Account Setup

1. **Create a Plaid Account:**
   - Go to [Plaid Dashboard](https://dashboard.plaid.com)
   - Sign up for a developer account (free sandbox access)
   - Create a new application

2. **Get API Credentials:**
   - Navigate to your application in the Plaid Dashboard
   - Copy your `client_id` and `secret` (sandbox credentials)

3. **Update Environment Variables:**
   ```bash
   # Add to your .env file
   PLAID_CLIENT_ID=your-plaid-client-id-from-dashboard
   PLAID_SECRET=your-plaid-secret-from-dashboard
   PLAID_ENV=sandbox
   PLAID_PRODUCTS=["transactions", "accounts", "identity", "liabilities", "investments"]
   ```

### Testing Plaid MCP Integration

The application includes a comprehensive test suite for validating the complete Plaid integration through the MCP server.

#### What the test validates:

1. **Plaid Sandbox Setup**: Creates test public tokens using Plaid's sandbox API
2. **MCP Authentication**: Verifies JWT authentication works with MCP server  
3. **Token Exchange**: Tests public token → access token exchange via MCP tools
4. **Account Data**: Retrieves account information through MCP tools
5. **Transaction Data**: Fetches transaction history via MCP tools (with proper sync)
6. **Balance Data**: Gets real-time balance information through MCP tools
7. **Identity & Investment Data**: Tests additional Plaid endpoints (identity, liabilities, investments)

#### Prerequisites for testing:

- **Plaid sandbox credentials** configured in `.env` file
- **FastAPI server running** at `http://localhost:8000`

#### Running the test:

```bash
# From backend directory
cd backend

# Start the FastAPI server (in separate terminal)
python -m uvicorn app.main:app --reload

# Run the comprehensive Plaid MCP test
python test_mcp_plaid.py
```

#### Expected output:

```
🚀 Comprehensive Plaid MCP Integration Test Suite
============================================================
🕐 Test started at: 2025-09-02 23:09:18

🔐 MCP Authentication Test
==================================================

📝 Testing without authentication (expect 401)...
------------------------------
✅ Correctly rejected (401 Unauthorized)

📝 Testing with JWT authentication...
------------------------------
🎫 Generated token: eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...
✅ Successfully authenticated and retrieved 12 tools

🏦 Plaid Sandbox Setup Test
==================================================

📝 Creating sandbox public token...
------------------------------
✅ Successfully created public token: public-sandbox-ab4b711c-44e3-4...
📋 Request ID: rdVEh1q6mHcirKM

🔗 MCP Plaid Integration Test
==================================================

📋 Getting available MCP tools...
------------------------------
  • mcp_health_check: Check MCP server health status.

Returns:
    Dictionary con...
  • echo: Echo the input message back.

Args:
    message: Message to ...
  • get_current_time: Get the current time.

Args:
    timezone: Timezone (current...
  • whoami: Get information about the authenticated user from JWT token....
  • create_link_token: Create a Plaid Link token for user authentication.

Args:
  ...
  • exchange_public_token: Exchange Plaid public token for access token and store it fo...
  • get_accounts: Get authenticated user's connected bank accounts from all in...
  • get_all_transactions: Get ALL transactions for authenticated user using sync endpo...
  • get_balances: Get real-time account balances for authenticated user.

Args...
  • get_identity: Get identity information for authenticated user's connected ...
  • get_liabilities: Get liability accounts for authenticated user's connected in...
  • get_investments: Get investment accounts and holdings for authenticated user....

🏦 Found 8 Plaid tools: create_link_token, exchange_public_token, get_accounts, get_all_transactions, get_balances, get_identity, get_liabilities, get_investments

💱 Test 1: Exchange public token
------------------------------
📤 Input: Created public token from sandbox
📥 Output: "{\"status\":\"success\",\"item_id\":\"4o3NebA96ps5KNyXd8E8SGAyMRQLlvsdJKebK\",\"request_id\":\"hwU5r1thHIfhc2v\",\"message\":\"Account successfully connected\"}"
✅ Public token exchange successful

💼 Test 2: Get accounts
------------------------------
📤 Input: (no arguments - uses authenticated user context)
📥 Output: {
  "status": "success",
  "accounts": [
    {
      "account_id": "nzXakD6Z4bFG7zrvXbKbTw3EL11EV7FAg7xkA",
      "name": "Plaid Checking",
      "type": "depository",
      "subtype": "checking",
      "mask": "0000",
      "balances": {
        "current": 110.0,
        "available": 100.0,
        "limit": null,
        "currency": "USD"
      }
    },
    {
      "account_id": "bJavAXRBpwFGJB7VZ141TpQKkRRKE9tmr9DLo",
      "name": "Plaid Saving",
      "type": "depository",
      "subtype": "savings",
      "mask": "1111",
      "balances": {
        "current": 210.0,
        "available": 200.0,
        "limit": null,
        "currency": "USD"
      }
    },
    {
      "account_id": "mkedzD6QJauEwkKvZbqbheXNgLLNpKhg8KqjM",
      "name": "Plaid CD",
      "type": "depository",
      "subtype": "cd",
      "mask": "2222",
      "balances": {
        "current": 1000.0,
        "available": null,
        "limit": null,
        "currency": "USD"
      }
    },
    {
      "account_id": "yeaLQK6GdDt9A3zw7pjpS1edmMMdNpF4p1NdD",
      "name": "Plaid Credit Card",
      "type": "credit",
      "subtype": "credit card",
      "mask": "3333",
      "balances": {
        "current": 410.0,
        "available": null,
        "limit": 2000.0,
        "currency": "USD"
      }
    },
    {
      "account_id": "9AvQL7oqk5FNmo1PeqaqF6eLMZZLJPC4MeP8n",
      "name": "Plaid Money Market",
      "type": "depository",
      "subtype": "money market",
      "mask": "4444",
      "balances": {
        "current": 43200.0,
        "available": 43200.0,
        "limit": null,
        "currency": "USD"
      }
    },
    {
      "account_id": "J5GvrxyMkQCDA9gymM5MuPmDln8l3DCBwK7j1",
      "name": "Plaid IRA",
      "type": "investment",
      "subtype": "ira",
      "mask": "5555",
      "balances": {
        "current": 320.76,
        "available": null,
        "limit": null,
        "currency": "USD"
      }
    },
    {
      "account_id": "kqe3KDR7wpF6oqlvde1eINWeDXdD4eFLAGPEm",
      "name": "Plaid 401k",
      "type": "investment",
      "subtype": "401k",
      "mask": "6666",
      "balances": {
        "current": 23631.9805,
        "available": null,
        "limit": null,
        "currency": "USD"
      }
    },
    {
      "account_id": "lKXxrDRe7JFGVKk8g9l9T8PvgWag1vip6z9WN",
      "name": "Plaid Student Loan",
      "type": "loan",
      "subtype": "student",
      "mask": "7777",
      "balances": {
        "current": 65262.0,
        "available": null,
        "limit": null,
        "currency": "USD"
      }
    },
    {
      "account_id": "qxmPdD6LlqCW7x3vANnNSnDmP9XPBmfgBvbWB",
      "name": "Plaid Mortgage",
      "type": "loan",
      "subtype": "mortgage",
      "mask": "8888",
      "balances": {
        "current": 56302.06,
        "available": null,
        "limit": null,
        "currency": "USD"
      }
    },
    {
      "account_id": "K5evzdL1RyCpoyAV6151CQL1pg4px1cRr7w83",
      "name": "Plaid HSA",
      "type": "depository",
      "subtype": "hsa",
      "mask": "9001",
      "balances": {
        "current": 6009.0,
        "available": 6009.0,
        "limit": null,
        "currency": "USD"
      }
    },
    {
      "account_id": "rdLkaD6pqKiG6dAVD737TZpjrKyrgjC7NWKwq",
      "name": "Plaid Cash Management",
      "type": "depository",
      "subtype": "cash management",
      "mask": "9002",
      "balances": {
        "current": 12060.0,
        "available": 12060.0,
        "limit": null,
        "currency": "USD"
      }
    },
    {
      "account_id": "9AvQL7oqk5FNmo1PeqaqF6eLJr4JkLf4MeP87",
      "name": "Plaid Business Credit Card",
      "type": "credit",
      "subtype": "credit card",
      "mask": "9999",
      "balances": {
        "current": 5020.0,
        "available": 4980.0,
        "limit": 10000.0,
        "currency": "USD"
      }
    }
  ],
  "institutions": [
    {
      "institution_id": "ins_109508",
      "item_id": "4o3NebA96ps5KNyXd8E8SGAyMRQLlvsdJKebK"
    }
  ],
  "total_accounts": 12
}
✅ Retrieved 12 accounts
   Account 1: Plaid Checking (depository) - Balance: $110.0
   Account 2: Plaid Saving (depository) - Balance: $210.0
   Account 3: Plaid CD (depository) - Balance: $1000.0

📊 Test 3: Get all transactions
------------------------------
📤 Input: (no cursor - full sync with polling)
✅ Retrieved 16 transactions
   Note: Retrieved 16 transactions using sync endpoint
   TX 1: $500.0 - United Airlines (2025-09-01)
   TX 2: $6.33 - Uber 072515 SF**POOL** (2025-08-30)
   TX 3: $500.0 - Tectra Inc (2025-08-27)

💰 Test 4: Get balances
------------------------------
📤 Input: (no arguments)
✅ Retrieved balances for 12 accounts
   Plaid Checking: $110.0
   Plaid Saving: $210.0
   Plaid CD: $1000.0
   Plaid Credit Card: $410.0
   Plaid Money Market: $43200.0
   Plaid IRA: $320.76
   Plaid 401k: $23631.9805
   Plaid Student Loan: $65262.0
   Plaid Mortgage: $56302.06
   Plaid HSA: $6009.0
   Plaid Cash Management: $12060.0
   Plaid Business Credit Card: $5020.0
💵 Total balance across all accounts: $213535.8005

🆔 Test 5: Get identity
------------------------------
📤 Input: (no arguments)
✅ Retrieved identity information for 12 accounts
   Account: Plaid Checking
     Name: Alberta Bobbeth Charleson
     Email: accountholder0@example.com
   Account: Plaid Saving
     Name: Alberta Bobbeth Charleson
     Email: accountholder0@example.com

💳 Test 6: Get liabilities
------------------------------
📤 Input: (no arguments)
✅ Retrieved liability information for 12 accounts
   • Credit cards: 1
   • Mortgages: 1
   • Student loans: 1
   Account 1: Plaid Checking (depository/checking) - Balance: $110.0
   Account 2: Plaid Saving (depository/savings) - Balance: $210.0

📈 Test 7: Get investments
------------------------------
📤 Input: (no arguments)
✅ Retrieved investment information for 12 accounts
   • Holdings: 13
   • Securities: 13
   • Total portfolio value: $25,446.39
   Account 1: Plaid Checking (depository/checking) - Balance: $110.0
   Account 2: Plaid Saving (depository/savings) - Balance: $210.0
   Holding 1: Security d6ePmbPxgWCWmMVv66q9iPV94n91vMtov5Are - Qty: 0.01, Value: $0.01
   Holding 2: Security KDwjlXj1Rqt58dVvmzRguxJybmyQL8FgeWWAy - Qty: 1.0, Value: $2.11
   Holding 3: Security NDVQrXQoqzt5v3bAe8qRt4A7mK7wvZCLEBBJk - Qty: 2.0, Value: $20.84

============================================================
✅ All Plaid MCP integration tests completed successfully!
🎯 Complete flow working: Sandbox → MCP → Plaid API
🔧 MCP tools successfully integrated with Plaid service
🔐 JWT authentication working correctly
🏦 Plaid sandbox integration functional
```

#### Troubleshooting:

**MCP Server Not Running:**
```
❌ Error during testing: Connection refused
💡 Make sure the FastAPI server is running:
   python -m uvicorn app.main:app --reload
```

**Plaid Credentials Missing:**
```
❌ Failed to create sandbox public token
💡 Make sure Plaid credentials are set:
   export PLAID_CLIENT_ID='your_client_id'
   export PLAID_SECRET='your_secret'
```

**Import Errors:**
```
❌ langchain-mcp-adapters not installed
```
Run: `uv sync` to install all dependencies

This test validates that AI agents will be able to access real financial data through the MCP server with proper authentication and user context.





