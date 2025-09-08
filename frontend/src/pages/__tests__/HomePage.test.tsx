import { screen } from '@testing-library/react'
import HomePage from '../HomePage'
import { renderWithProviders } from '../../tests/setupTests'

describe('HomePage', () => {
  test('renders welcome title', () => {
    renderWithProviders(<HomePage />)
    expect(screen.getByText('Welcome to AI Financial Assistant')).toBeInTheDocument()
  })

  test('renders subtitle description', () => {
    renderWithProviders(<HomePage />)
    expect(screen.getByText(/Your intelligent companion for managing finances/)).toBeInTheDocument()
  })

  test('renders feature cards', () => {
    renderWithProviders(<HomePage />)
    expect(screen.getByText('Smart Analytics')).toBeInTheDocument()
    expect(screen.getByText('Secure Banking')).toBeInTheDocument()
    expect(screen.getByText('Personalized Advice')).toBeInTheDocument()
  })

  test('renders feature descriptions', () => {
    renderWithProviders(<HomePage />)
    expect(screen.getByText(/Get AI-powered insights/)).toBeInTheDocument()
    expect(screen.getByText(/Connect your bank accounts securely/)).toBeInTheDocument()
    expect(screen.getByText(/Receive tailored financial recommendations/)).toBeInTheDocument()
  })
})