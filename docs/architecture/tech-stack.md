# Tech Stack

This is the DEFINITIVE technology selection for the entire project. All development must use these exact versions and configurations.

## Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Frontend Language** | TypeScript | 5.3.x | Type-safe frontend development | Essential for financial app reliability and Redux integration |
| **Frontend Framework** | React | 18.2.x | User interface framework | Mature ecosystem, excellent AI-SDK integration |
| **UI Component Library** | Styled Components | 6.1.x | Component styling and theming | Consistent design system implementation |
| **State Management** | Redux Toolkit | 1.9.x | Predictable state management | Complex financial data flows require predictable state |
| **Backend Language** | Python | 3.11.x | Server-side development | Excellent AI/ML ecosystem, FastAPI compatibility |
| **Backend Framework** | FastAPI | 0.104.x | API framework with auto-docs | Async support, automatic OpenAPI generation, security features |
| **API Style** | REST | OpenAPI 3.0 | Client-server communication | Simple, well-understood, excellent tooling |
| **Database** | In-Memory Dict | POC Only | Data storage for POC | Simplifies POC development, Redis-compatible transition path |
| **Cache** | In-Memory | POC Only | Session and conversation caching | Sufficient for POC user load |
| **Authentication** | Google OAuth + JWT | OAuth 2.0 | User authentication and session management | Trusted provider, reduces password management |
| **Frontend Testing** | Jest + Testing Library | Latest | Component and integration testing | React ecosystem standard |
| **Backend Testing** | Pytest + httpx | Latest | API and business logic testing | Python standard with async support |
| **Build Tool** | Vite | 5.0.x | Frontend build and dev server | Fast development experience, modern tooling |
| **Bundler** | Vite (esbuild) | Built-in | JavaScript bundling and optimization | Superior performance for development iterations |
| **CSS Framework** | Styled Components + Theme | 6.1.x | Styling architecture | Component-scoped styling with theming support |
| **AI Framework** | LangGraph | 0.0.x | Multi-agent conversation orchestration | Specialized agent routing with shared conversation state |
| **Frontend AI** | AI-SDK | 2.2.x | React AI conversation interface | Seamless streaming AI integration with React |
| **Financial API** | Plaid | Latest | Bank account and transaction data | Industry standard for financial data aggregation |
| **Market Data API (Primary)** | Alpha Vantage | Latest | Real-time stock/ETF prices and fundamentals | Free tier sufficient for MVP, comprehensive data coverage |
| **Market Data API (Secondary)** | Finnhub | Latest | Sector performance and market insights | Complements Alpha Vantage with sector analysis |
| **API Client** | RTK Query | Built-in RTK | Frontend API state management | Integrated caching and state management |
| **Container** | Docker | 24.x | Development and deployment consistency | Consistent environments across development/production |
| **Package Manager** | UV | Latest | Python dependency management | Modern, fast Python dependency resolution |
| **Agent Orchestration** | LangGraph Multi-Agent | 0.0.x | Agentic AI conversation orchestration | Specialized agents with unified orchestration |
| **Tool Protocol** | MCP Python SDK | Latest | Model Context Protocol server | Centralized tool access for multiple agents |
| **Graph Database** | Graphiti | Latest | Contextual memory and relationship storage | Enhanced context retention across agent interactions |
