import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import LoginPage from '../LoginPage'
import { renderWithProviders } from '../../tests/setupTests'

// Mock the API
const mockLogin = jest.fn()
const mockRegister = jest.fn()
const mockNavigate = jest.fn()

jest.mock('../../store/api/generated', () => ({
  ...jest.requireActual('../../store/api/generated'),
  useLoginAuthLoginPostMutation: () => [mockLogin, { isLoading: false, error: null }],
  useRegisterAuthRegisterPostMutation: () => [mockRegister, { isLoading: false, error: null }],
}))

// Mock Navigate component
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  Navigate: ({ to }: { to: string }) => {
    mockNavigate(to)
    return <div data-testid="navigate">{to}</div>
  },
}))


describe('LoginPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockLogin.mockReturnValue({ unwrap: jest.fn().mockResolvedValue({}) })
    mockRegister.mockReturnValue({ unwrap: jest.fn().mockResolvedValue({}) })
    mockNavigate.mockClear()
  })

  it('renders login form by default', async () => {
    renderWithProviders(<LoginPage />)

    const match = await screen.findAllByText('Sign In')
    expect(match).toHaveLength(2)
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.queryByLabelText(/full name/i)).not.toBeInTheDocument()
  })

  it('switches to register form when toggle is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    await user.click(screen.getByText(/sign up/i))

    const match = await screen.findAllByText('Create Account')

    expect(match).toHaveLength(2)
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('validates required fields on login', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(screen.getByText('Email is required')).toBeInTheDocument()
    expect(screen.getByText('Password is required')).toBeInTheDocument()
  })

  it('validates password strength on registration', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    // Switch to register mode
    await user.click(screen.getByText(/sign up/i))

    await user.type(screen.getByLabelText(/full name/i), 'John Doe')
    await user.type(screen.getByLabelText(/email address/i), 'john@example.com')
    await user.type(screen.getByLabelText(/password/i), 'weak')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    expect(screen.getByText(/Password must have:/)).toBeInTheDocument()
  })

  it('shows password requirements in register mode', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    await user.click(screen.getByText(/sign up/i))

    expect(screen.getByText('Password must contain:')).toBeInTheDocument()
    expect(screen.getByText('At least 8 characters')).toBeInTheDocument()
    expect(screen.getByText('One lowercase letter')).toBeInTheDocument()
    expect(screen.getByText('One uppercase letter')).toBeInTheDocument()
    expect(screen.getByText('One number')).toBeInTheDocument()
    expect(screen.getByText(/One special character/)).toBeInTheDocument()
  })

  it('submits login form with valid data', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    await user.type(screen.getByLabelText(/email address/i), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(mockLogin).toHaveBeenCalledWith({
      loginRequest: {
        email: 'test@example.com',
        password: 'password123',
      },
    })
  })

  it('submits register form with valid data', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    // Switch to register mode
    await user.click(screen.getByText(/sign up/i))

    await user.type(screen.getByLabelText(/full name/i), 'John Doe')
    await user.type(screen.getByLabelText(/email address/i), 'john@example.com')
    await user.type(screen.getByLabelText(/password/i), 'StrongPass123!')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    expect(mockRegister).toHaveBeenCalledWith({
      registerRequest: {
        email: 'john@example.com',
        password: 'StrongPass123!',
        name: 'John Doe',
      },
    })
  })

  it('clears form when switching between modes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    // Fill login form
    await user.type(screen.getByLabelText(/email address/i), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password')

    // Switch to register mode
    await user.click(screen.getByText(/sign up/i))

    // Fields should be cleared
    expect(screen.getByLabelText(/email address/i)).toHaveValue('')
    expect(screen.getByLabelText(/password/i)).toHaveValue('')
    expect(screen.getByLabelText(/full name/i)).toHaveValue('')
  })

  it('clears field errors when user starts typing', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    // Trigger validation error
    await user.click(screen.getByRole('button', { name: /sign in/i }))
    expect(screen.getByText('Email is required')).toBeInTheDocument()

    // Start typing to clear error
    await user.type(screen.getByLabelText(/email address/i), 'test')
    expect(screen.queryByText('Email is required')).not.toBeInTheDocument()
  })

  it('redirects to home if already authenticated', () => {
    renderWithProviders(<LoginPage />, {
      auth: {
        user: { id: '1', email: 'test@example.com', profile_complete: false },
        token: 'fake-token',
        isAuthenticated: true,
        loading: false,
      },
    })

    expect(mockNavigate).toHaveBeenCalledWith('/')
    expect(screen.getByTestId('navigate')).toBeInTheDocument()
    expect(screen.getByText('/')).toBeInTheDocument()
  })
})