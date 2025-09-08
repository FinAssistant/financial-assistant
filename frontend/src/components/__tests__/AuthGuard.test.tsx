import { screen } from '@testing-library/react'

import AuthGuard from '../layout/AuthGuard'
import { renderWithProviders } from '../../tests/setupTests'

// Mock Navigate component
const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  Navigate: ({ to, state }: { to: string; state?: unknown }) => {
    mockNavigate(to, state)
    return <div data-testid="navigate" data-to={to}>Navigating to {to}</div>
  },
}))


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

      expect(screen.getByText('Checking authentication...')).toBeInTheDocument()
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
        {
          pathname: '/login',
          state: { from: { pathname: '/protected-page' } }
        }
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

      expect(screen.getByText('Checking authentication...')).toBeInTheDocument()
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })
  })
})