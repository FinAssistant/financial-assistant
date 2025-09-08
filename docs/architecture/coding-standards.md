# Coding Standards

## Critical Fullstack Rules

- **Type Sharing**: Always define types in frontend/src/types and ensure backend Pydantic models match
- **API Calls**: Never make direct HTTP calls - use RTK Query service layer
- **Environment Variables**: Access only through config objects, never process.env directly
- **Error Handling**: All API routes must use the standard error handler
- **State Updates**: Never mutate state directly - use proper Redux patterns
- **Plaid Security**: Never expose access tokens in frontend, always encrypt in backend
- **AI Conversations**: Always use AI-SDK for streaming, never direct API calls

## Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| Components | PascalCase | - | `UserProfile.tsx` |
| Hooks | camelCase with 'use' | - | `useAuth.ts` |
| API Routes | - | kebab-case | `/api/user-profile` |
| Python Classes | - | PascalCase | `UserProfile` |
| Python Functions | - | snake_case | `get_user_profile()` |
