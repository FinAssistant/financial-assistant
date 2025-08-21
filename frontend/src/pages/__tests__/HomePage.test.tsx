import { render, screen } from '@testing-library/react'
import { ThemeProvider } from 'styled-components'
import HomePage from '../HomePage'
import { theme } from '../../styles/theme'

const renderHomePage = () => {
  return render(
    <ThemeProvider theme={theme}>
      <HomePage />
    </ThemeProvider>
  )
}

describe('HomePage', () => {
  test('renders welcome title', () => {
    renderHomePage()
    expect(screen.getByText('Welcome to AI Financial Assistant')).toBeInTheDocument()
  })

  test('renders subtitle description', () => {
    renderHomePage()
    expect(screen.getByText(/Your intelligent companion for managing finances/)).toBeInTheDocument()
  })

  test('renders feature cards', () => {
    renderHomePage()
    expect(screen.getByText('Smart Analytics')).toBeInTheDocument()
    expect(screen.getByText('Secure Banking')).toBeInTheDocument()
    expect(screen.getByText('Personalized Advice')).toBeInTheDocument()
  })

  test('renders feature descriptions', () => {
    renderHomePage()
    expect(screen.getByText(/Get AI-powered insights/)).toBeInTheDocument()
    expect(screen.getByText(/Connect your bank accounts securely/)).toBeInTheDocument()
    expect(screen.getByText(/Receive tailored financial recommendations/)).toBeInTheDocument()
  })
})