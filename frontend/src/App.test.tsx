import { screen } from '@testing-library/react'
import App from './App'
import { renderWithProviders } from './tests/setupTests'

describe('App', () => {
  test('renders without crashing', () => {
    renderWithProviders(<App />)
  })

  test('renders header with app name', () => {
    renderWithProviders(<App />)
    expect(screen.getByText('AI Financial Assistant')).toBeInTheDocument()
  })

  test('renders navigation links', () => {
    renderWithProviders(<App />)
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()
  })
})