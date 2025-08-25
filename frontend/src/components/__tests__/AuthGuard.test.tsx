import React from 'react'
import { render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from 'styled-components'
import { configureStore } from '@reduxjs/toolkit'

import AuthGuard from '../layout/AuthGuard'
import { baseApi } from '../../store/api/baseApi'
import authReducer from '../../store/slices/authSlice'
import { theme } from '../../styles/theme'

// Mock Navigate component
const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  Navigate: ({ to, state }: { to: string; state?: unknown }) => {
    mockNavigate(to, state)
    return <div data-testid="navigate" data-to={to}>Navigating to {to}</div>
  },
}))

// Create a test store
const createTestStore = (initialState: { auth?: Partial<{ user: null | { id: string; email: string; profile_complete: boolean }, token: null | string, isAuthenticated: boolean, loading: boolean }> } = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      [baseApi.reducerPath]: baseApi.reducer,
    },
    preloadedState: {
      auth: {
        user: null,
        token: null,
        isAuthenticated: false,
        loading: false,
        ...initialState.auth,
      },
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(baseApi.middleware),
  })
}

const renderWithProviders = (
  component: React.ReactElement,
  initialState = {},
  initialRoute = '/'
) => {
  const store = createTestStore(initialState)

  return render(
    <Provider store={store}>
      <MemoryRouterfuture={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }} initialEntries={[initialRoute]}>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </MemoryRouter>
    </Provider >
  )
}

const TestComponent = () => <div>Protected Content</div>

describe('AuthGuard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('when requireAuth is true (default)', () => {
    it('shows loading spinner when authentication is loading', () => {
      renderWithProviders(
        <AuthGuard>
          <TestComponent />
        </AuthGuard>,
        {
          auth: {
            user: null,
            token: null,
            isAuthenticated: false,
            loading: true,
          },
        }
      )

      expect(screen.getByText('Loading...')).toBeInTheDocument()
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })

    it('renders children when user is authenticated', () => {
      renderWithProviders(
        <AuthGuard>
          <TestComponent />
        </AuthGuard>,
        {
          auth: {
            user: { id: '1', email: 'test@example.com', profile_complete: false },
            token: 'fake-token',
            isAuthenticated: true,
            loading: false,
          },
        }
      )

      expect(screen.getByText('Protected Content')).toBeInTheDocument()
      expect(screen.queryByTestId('navigate')).not.toBeInTheDocument()
    })

    it('redirects to login when user is not authenticated', () => {
      renderWithProviders(
        <AuthGuard>
          <TestComponent />
        </AuthGuard>,
        {
          auth: {
            user: null,
            token: null,
            isAuthenticated: false,
            loading: false,
          },
        },
        '/protected-page'
      )

      expect(screen.getByTestId('navigate')).toBeInTheDocument()
      expect(screen.getByText('Navigating to /login')).toBeInTheDocument()
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
      expect(mockNavigate).toHaveBeenCalledWith('/login', {
        from: expect.objectContaining({ pathname: '/protected-page' })
      })
    })

    it('uses custom redirect path', () => {
      renderWithProviders(
        <AuthGuard redirectTo="/custom-login">
          <TestComponent />
        </AuthGuard>,
        {
          auth: {
            user: null,
            token: null,
            isAuthenticated: false,
            loading: false,
          },
        }
      )

      expect(screen.getByText('Navigating to /custom-login')).toBeInTheDocument()
      expect(mockNavigate).toHaveBeenCalledWith('/custom-login', expect.any(Object))
    })
  })

  describe('when requireAuth is false', () => {
    it('renders children when user is not authenticated', () => {
      renderWithProviders(
        <AuthGuard requireAuth={false}>
          <TestComponent />
        </AuthGuard>,
        {
          auth: {
            user: null,
            token: null,
            isAuthenticated: false,
            loading: false,
          },
        }
      )

      expect(screen.getByText('Protected Content')).toBeInTheDocument()
      expect(screen.queryByTestId('navigate')).not.toBeInTheDocument()
    })

    it('redirects authenticated users to home page', () => {
      renderWithProviders(
        <AuthGuard requireAuth={false}>
          <TestComponent />
        </AuthGuard>,
        {
          auth: {
            user: { id: '1', email: 'test@example.com', profile_complete: false },
            token: 'fake-token',
            isAuthenticated: true,
            loading: false,
          },
        },
        '/login'
      )

      expect(screen.getByTestId('navigate')).toBeInTheDocument()
      expect(screen.getByText('Navigating to /')).toBeInTheDocument()
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
      expect(mockNavigate).toHaveBeenCalledWith('/', undefined)
    })

    it('redirects authenticated users to intended page from location state', () => {
      const TestComponentWithLocationState = () => (
        <AuthGuard requireAuth={false}>
          <TestComponent />
        </AuthGuard>
      )

      render(
        <Provider store={createTestStore({
          auth: {
            user: { id: '1', email: 'test@example.com', profile_complete: false },
            token: 'fake-token',
            isAuthenticated: true,
            loading: false,
          },
        })}>
          <MemoryRouter
            initialEntries={[
              {
                pathname: '/login',
                state: { from: { pathname: '/protected-page' } }
              }
            ]}
          >
            <ThemeProvider theme={theme}>
              <TestComponentWithLocationState />
            </ThemeProvider>
          </MemoryRouter>
        </Provider>
      )

      expect(screen.getByText('Navigating to /protected-page')).toBeInTheDocument()
      expect(mockNavigate).toHaveBeenCalledWith('/protected-page', undefined)
    })

    it('shows loading spinner when authentication is loading', () => {
      renderWithProviders(
        <AuthGuard requireAuth={false}>
          <TestComponent />
        </AuthGuard>,
        {
          auth: {
            user: null,
            token: null,
            isAuthenticated: false,
            loading: true,
          },
        }
      )

      expect(screen.getByText('Loading...')).toBeInTheDocument()
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })
  })
})