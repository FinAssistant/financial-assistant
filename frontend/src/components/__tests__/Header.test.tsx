import { screen } from '@testing-library/react'
import Header from '../Header'
import { renderWithProviders } from '../../tests/setupTests'

// Mock the API
const mockLogout = jest.fn()

jest.mock('../../store/api/generated', () => ({
  ...jest.requireActual('../../store/api/generated'),
  useLogoutAuthLogoutPostMutation: () => [mockLogout, { isLoading: false }],
}))


describe('Header', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockLogout.mockReturnValue({ unwrap: jest.fn().mockResolvedValue({}) })
  })

  test('renders app name as logo', () => {
    renderWithProviders(<Header />)
    expect(screen.getByText('AI Financial Assistant')).toBeInTheDocument()
  })

  test('renders navigation links', () => {
    renderWithProviders(<Header />)
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()
  })

  test('logo links to home page', () => {
    renderWithProviders(<Header />)
    const logo = screen.getByText('AI Financial Assistant')
    expect(logo.closest('a')).toHaveAttribute('href', '/')
  })

  test('navigation links have correct hrefs', () => {
    renderWithProviders(<Header />)
    const homeLink = screen.getByText('Home')
    const aboutLink = screen.getByText('About')

    expect(homeLink.closest('a')).toHaveAttribute('href', '/')
    expect(aboutLink.closest('a')).toHaveAttribute('href', '/about')
  })

  test('shows sign in button when not authenticated', () => {
    renderWithProviders(<Header />)
    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByText('Sign In').closest('a')).toHaveAttribute('href', '/login')
  })

  test('shows user info and logout button when authenticated', () => {
    renderWithProviders(<Header />, {
      auth: {
        user: { id: '1', email: 'test@example.com', name: 'Test User', profile_complete: true },
        token: 'fake-token',
        isAuthenticated: true,
        loading: false,
      },
    })

    expect(screen.getByText('Hello, Test User')).toBeInTheDocument()
    expect(screen.getByText('Logout')).toBeInTheDocument()
    expect(screen.queryByText('Sign In')).not.toBeInTheDocument()
  })
})