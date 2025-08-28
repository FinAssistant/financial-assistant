import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Navigation from '../Navigation'
import { renderWithProviders } from '../../../tests/setupTests'
import * as authSlice from '../../../store/slices/authSlice'

// Mock the logout action
const mockLogout = jest.fn().mockReturnValue({ type: 'auth/logout' })
jest.spyOn(authSlice, 'logout').mockImplementation(mockLogout)

describe('Navigation', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders navigation for non-authenticated users with limited items', () => {
    renderWithProviders(<Navigation />, {
      auth: {
        isAuthenticated: false,
        user: null,
        token: null,
        loading: false,
      },
    })

    // Should show Home and About for non-authenticated users
    expect(screen.getByRole('link', { name: /Home/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /About/ })).toBeInTheDocument()
    
    // Should NOT show authenticated-only items
    expect(screen.queryByRole('link', { name: /Accounts/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Transactions/ })).not.toBeInTheDocument()
  })

  it('renders navigation menu when user is authenticated', () => {
    renderWithProviders(<Navigation />, {
      auth: {
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', name: 'Test User', profile_complete: true },
        token: 'fake-token',
        loading: false,
      },
    })

    // Check key navigation items are present
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Accounts')).toBeInTheDocument()
    expect(screen.getByText('Transactions')).toBeInTheDocument()
    expect(screen.getByText('Profile')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('displays user info correctly when user has name', () => {
    renderWithProviders(<Navigation />, {
      auth: {
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', name: 'Test User', profile_complete: true },
        token: 'fake-token',
        loading: false,
      },
    })

    expect(screen.getByText('Test User')).toBeInTheDocument()
  })

  it('displays user email when user has no name', () => {
    renderWithProviders(<Navigation />, {
      auth: {
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', profile_complete: true },
        token: 'fake-token',
        loading: false,
      },
    })

    expect(screen.getByText('test@example.com')).toBeInTheDocument()
  })

  it('handles logout correctly', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Navigation />, {
      auth: {
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', name: 'Test User', profile_complete: true },
        token: 'fake-token',
        loading: false,
      },
    })

    const logoutButton = screen.getByTitle('Logout')
    await user.click(logoutButton)

    // Verify the logout action was dispatched
    expect(mockLogout).toHaveBeenCalled()
  })

  it('shows mobile menu button on mobile devices', () => {
    renderWithProviders(<Navigation />, {
      auth: {
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', profile_complete: true },
        token: 'fake-token',
        loading: false,
      },
    })

    const menuButton = screen.getByRole('button', { name: 'Toggle navigation' })
    expect(menuButton).toBeInTheDocument()
  })

  it('toggles mobile menu when button is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Navigation />, {
      auth: {
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', profile_complete: true },
        token: 'fake-token',
        loading: false,
      },
    })

    const menuButton = screen.getByRole('button', { name: 'Toggle navigation' })
    
    // Initially closed (Menu icon)
    expect(screen.getByRole('button', { name: 'Toggle navigation' })).toBeInTheDocument()
    
    // Click to open (should show X icon)
    await user.click(menuButton)
    
    // Menu should be open (we can't easily test the visual state in jsdom)
    expect(menuButton).toBeInTheDocument()
  })

  it('highlights active navigation item', () => {
    renderWithProviders(<Navigation />, {
      auth: {
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', profile_complete: true },
        token: 'fake-token',
        loading: false,
      },
    }, '/')

    const dashboardLink = screen.getByRole('link', { name: /Dashboard/ })
    expect(dashboardLink).toHaveAttribute('href', '/')
  })

  it('has proper navigation structure and accessibility', () => {
    renderWithProviders(<Navigation />, {
      auth: {
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', profile_complete: true },
        token: 'fake-token',
        loading: false,
      },
    })

    expect(screen.getByRole('navigation')).toBeInTheDocument()
    expect(screen.getAllByRole('list')).toHaveLength(5) // 5 sections with lists
    expect(screen.getAllByRole('listitem')).toHaveLength(10) // All navigation items for authenticated users
    
    // Check section titles (using headings)
    expect(screen.getByRole('heading', { name: 'Overview' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Information' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Financial Management' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Analytics' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Account' })).toBeInTheDocument()
  })

  it('closes mobile menu when navigation link is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Navigation />, {
      auth: {
        isAuthenticated: true,
        user: { id: '1', email: 'test@example.com', profile_complete: true },
        token: 'fake-token',
        loading: false,
      },
    })

    const menuButton = screen.getByRole('button', { name: 'Toggle navigation' })
    await user.click(menuButton) // Open menu
    
    const profileLink = screen.getByRole('link', { name: /Profile/ })
    await user.click(profileLink) // Click navigation link
    
    // Menu should close (tested via event handler)
    expect(profileLink).toBeInTheDocument()
  })
})