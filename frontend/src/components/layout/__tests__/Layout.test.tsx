import { screen } from '@testing-library/react'
import Layout from '../Layout'
import { renderWithProviders } from '../../../tests/setupTests'

// Mock the Navigation component since it has complex auth logic
jest.mock('../Navigation', () => ({
  __esModule: true,
  default: function MockNavigation() {
    return <div data-testid="navigation">Navigation</div>
  }
}))

describe('Layout', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders header and main content', () => {
    renderWithProviders(
      <Layout>
        <div>Test content</div>
      </Layout>
    )

    expect(screen.getByText('AI Financial Assistant')).toBeInTheDocument()
    expect(screen.getByText('Test content')).toBeInTheDocument()
  })

  it('shows navigation when user is authenticated and showNavigation is true', () => {
    renderWithProviders(
      <Layout showNavigation={true}>
        <div>Test content</div>
      </Layout>,
      {
        auth: {
          isAuthenticated: true,
          user: { id: '1', email: 'test@example.com', profile_complete: true },
          token: 'fake-token',
          loading: false,
        },
      }
    )

    expect(screen.getByTestId('navigation')).toBeInTheDocument()
  })

  it('hides navigation when user is not authenticated', () => {
    renderWithProviders(
      <Layout showNavigation={true}>
        <div>Test content</div>
      </Layout>,
      {
        auth: {
          isAuthenticated: false,
          user: null,
          token: null,
          loading: false,
        },
      }
    )

    expect(screen.queryByTestId('navigation')).not.toBeInTheDocument()
  })

  it('hides navigation when showNavigation is false', () => {
    renderWithProviders(
      <Layout showNavigation={false}>
        <div>Test content</div>
      </Layout>,
      {
        auth: {
          isAuthenticated: true,
          user: { id: '1', email: 'test@example.com', profile_complete: true },
          token: 'fake-token',
          loading: false,
        },
      }
    )

    expect(screen.queryByTestId('navigation')).not.toBeInTheDocument()
  })

  it('displays loading state when loading prop is true', () => {
    renderWithProviders(
      <Layout loading={true}>
        <div>Test content</div>
      </Layout>
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(screen.queryByText('Test content')).not.toBeInTheDocument()
  })

  it('displays error state when error prop is provided', () => {
    renderWithProviders(
      <Layout error="Something went wrong">
        <div>Test content</div>
      </Layout>
    )

    expect(screen.getByText('Error: Something went wrong')).toBeInTheDocument()
    expect(screen.queryByText('Test content')).not.toBeInTheDocument()
  })

  it('displays children when no loading or error state', () => {
    renderWithProviders(
      <Layout>
        <div>Test content</div>
      </Layout>
    )

    expect(screen.getByText('Test content')).toBeInTheDocument()
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
  })

  it('has proper semantic structure with header and main elements', () => {
    renderWithProviders(
      <Layout>
        <div>Test content</div>
      </Layout>
    )

    expect(screen.getByRole('banner')).toBeInTheDocument() // header
    expect(screen.getByRole('main')).toBeInTheDocument() // main
  })

  it('error message has proper accessibility role', () => {
    renderWithProviders(
      <Layout error="Test error">
        <div>Test content</div>
      </Layout>
    )

    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
})