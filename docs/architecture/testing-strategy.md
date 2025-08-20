# Testing Strategy

## Testing Pyramid

```text
E2E Tests
/        \
Integration Tests
/            \
Frontend Unit  Backend Unit
```

## Test Organization

### Frontend Tests
```text
frontend/src/
├── components/
│   └── __tests__/
│       ├── UserProfile.test.tsx
│       └── AIConversation.test.tsx
├── store/
│   └── __tests__/
│       ├── authSlice.test.ts
│       └── plaidApi.test.ts
└── utils/
    └── __tests__/
        └── validation.test.ts
```

### Backend Tests
```text
backend/tests/
├── test_auth.py
├── test_plaid.py
├── test_ai.py
├── test_analysis.py
└── integration/
    ├── test_onboarding_flow.py
    └── test_plaid_integration.py
```

## Test Examples

### Frontend Component Test
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { store } from '../store';
import UserProfile from '../components/UserProfile';

test('displays user profile information', () => {
  render(
    <Provider store={store}>
      <UserProfile />
    </Provider>
  );
  
  expect(screen.getByText('Financial Goals')).toBeInTheDocument();
  expect(screen.getByText('Risk Tolerance')).toBeInTheDocument();
});
```

### Backend API Test
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_conversation():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/conversation/send",
            json={"message": "Hello", "session_type": "onboarding"},
            headers={"Authorization": "Bearer test-token"}
        )
    assert response.status_code == 200
    assert "message" in response.json()
```
