import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from 'styled-components'
import Header from '../Header'
import { theme } from '../../styles/theme'

const renderHeader = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <Header />
      </ThemeProvider>
    </BrowserRouter>
  )
}

describe('Header', () => {
  test('renders app name as logo', () => {
    renderHeader()
    expect(screen.getByText('AI Financial Assistant')).toBeInTheDocument()
  })

  test('renders navigation links', () => {
    renderHeader()
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()
  })

  test('logo links to home page', () => {
    renderHeader()
    const logo = screen.getByText('AI Financial Assistant')
    expect(logo.closest('a')).toHaveAttribute('href', '/')
  })

  test('navigation links have correct hrefs', () => {
    renderHeader()
    const homeLink = screen.getByText('Home')
    const aboutLink = screen.getByText('About')
    
    expect(homeLink.closest('a')).toHaveAttribute('href', '/')
    expect(aboutLink.closest('a')).toHaveAttribute('href', '/about')
  })
})