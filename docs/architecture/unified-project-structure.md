# Unified Project Structure

```text
ai-financial-assistant/
├── frontend/                           # React TypeScript application
│   ├── src/
│   │   ├── components/                # React components
│   │   │   ├── common/                # Reusable UI components
│   │   │   │   ├── Button/
│   │   │   │   ├── Card/
│   │   │   │   ├── ProgressBar/
│   │   │   │   └── LoadingSpinner/
│   │   │   ├── onboarding/            # Wizard-specific components
│   │   │   │   ├── AIConversation/
│   │   │   │   ├── GoalSetting/
│   │   │   │   ├── PlaidConnect/
│   │   │   │   └── WizardProgress/
│   │   │   ├── dashboard/             # Post-onboarding components
│   │   │   │   ├── AccountCard/
│   │   │   │   ├── TransactionList/
│   │   │   │   ├── SpendingChart/
│   │   │   │   └── ProfileSummary/
│   │   │   └── layout/                # Layout components
│   │   │       ├── Header/
│   │   │       ├── Navigation/
│   │   │       └── AuthGuard/
│   │   ├── store/                     # Redux store
│   │   │   ├── index.ts               # Store configuration
│   │   │   ├── slices/
│   │   │   │   ├── authSlice.ts       # Authentication state
│   │   │   │   ├── onboardingSlice.ts # Wizard progress
│   │   │   │   ├── accountsSlice.ts   # Financial accounts
│   │   │   │   └── uiSlice.ts         # UI state
│   │   │   └── api/
│   │   │       ├── authApi.ts         # Auth endpoints
│   │   │       ├── plaidApi.ts        # Plaid integration
│   │   │       └── conversationApi.ts # AI conversation
│   │   ├── pages/                     # Page components
│   │   │   ├── LoginPage/
│   │   │   ├── OnboardingPage/
│   │   │   └── DashboardPage/
│   │   ├── hooks/                     # Custom React hooks
│   │   ├── utils/                     # Frontend utilities
│   │   ├── types/                     # TypeScript type definitions
│   │   └── styles/                    # Global styles and themes
│   ├── dist/                          # Built frontend files (served by FastAPI)
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── backend/                           # Python FastAPI application
│   ├── app/
│   │   ├── main.py                   # FastAPI application entry + static file serving
│   │   ├── models/                   # Data models
│   │   │   ├── __init__.py
│   │   │   ├── user.py              # User and UserProfile models
│   │   │   ├── financial.py         # Account and Transaction models
│   │   │   └── conversation.py      # Conversation models
│   │   ├── services/                # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py      # Authentication logic
│   │   │   ├── plaid_service.py     # Plaid integration
│   │   │   ├── ai_service.py        # LangGraph AI orchestration
│   │   │   ├── analysis_service.py  # Financial analysis
│   │   │   └── sync_service.py      # Periodic data sync
│   │   ├── routers/                 # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # Authentication endpoints
│   │   │   ├── conversation.py      # AI conversation endpoints
│   │   │   ├── plaid.py             # Plaid endpoints
│   │   │   ├── accounts.py          # Account management
│   │   │   └── analysis.py          # Financial analysis endpoints
│   │   ├── core/                    # Core configuration
│   │   │   ├── __init__.py
│   │   │   ├── config.py            # Application configuration
│   │   │   ├── security.py          # Security utilities
│   │   │   └── database.py          # In-memory data store
│   │   ├── ai/                      # AI-specific modules
│   │   │   ├── __init__.py
│   │   │   ├── langgraph_config.py  # LangGraph setup
│   │   │   ├── prompts.py           # AI prompts and templates
│   │   │   └── categorization.py    # Transaction categorization
│   │   ├── static/                  # Built frontend files
│   │   └── utils/                   # Backend utilities
│   │       ├── __init__.py
│   │       ├── encryption.py        # Data encryption utilities
│   │       └── validation.py        # Input validation
│   ├── tests/                       # Backend tests
│   │   ├── test_auth.py
│   │   ├── test_plaid.py
│   │   ├── test_ai.py
│   │   └── test_analysis.py
│   ├── pyproject.toml               # UV dependency management
│   └── uv.lock                      # UV lock file
├── scripts/                         # Development scripts
│   ├── dev-setup.sh                # Development environment setup
│   ├── start-dev.sh                # Start development servers
│   ├── build-frontend.sh           # Build and copy frontend
│   └── run-tests.sh                # Run all tests
├── Dockerfile                      # Single container for the application
├── docs/                           # Documentation
│   ├── prd.md                      # Product Requirements Document
│   ├── front-end-spec.md           # Frontend specification
│   └── fullstack-architecture.md   # This document
├── .env.example                    # Environment variables template
├── .gitignore
└── README.md
```
