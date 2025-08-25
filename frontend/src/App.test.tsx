import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Provider } from 'react-redux'
import { ThemeProvider } from 'styled-components'
import App from './App'
import { store } from './store'
import { theme } from './styles/theme'

const AppWrapper = ({ children }: { children: React.ReactNode }) => (
  <Provider store={store}>
    <BrowserRouter future={{
      v7_startTransition: true,
      v7_relativeSplatPath: true,
    }}>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </BrowserRouter>
  </Provider>
)

describe('App', () => {
  test('renders without crashing', () => {
    render(
      <AppWrapper>
        <App />
      </AppWrapper>
    )
  })

  test('renders header with app name', () => {
    render(
      <AppWrapper>
        <App />
      </AppWrapper>
    )

    expect(screen.getByText('AI Financial Assistant')).toBeInTheDocument()
  })

  test('renders navigation links', () => {
    render(
      <AppWrapper>
        <App />
      </AppWrapper>
    )

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()
  })
})