import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from 'styled-components'
import { configureStore } from '@reduxjs/toolkit'
import { persistStore } from 'redux-persist'
import { PersistGate } from 'redux-persist/integration/react'
import Header from '../Header'
import { baseApi } from '../../store/api/baseApi'
import authReducer from '../../store/slices/authSlice'
import { theme } from '../../styles/theme'

// Mock the API
const mockLogout = jest.fn()

jest.mock('../../store/api/authApi', () => ({
  ...jest.requireActual('../../store/api/authApi'),
  useLogoutAuthLogoutPostMutation: () => [mockLogout, { isLoading: false }],
}))

// Create a test store
const createTestStore = (initialState: { auth?: Partial<{ user: null | { id: string; email: string; name?: string; profile_complete: boolean }, token: null | string, isAuthenticated: boolean, loading: boolean }> } = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      [baseApi.reducerPath]: baseApi.reducer,
    },
    preloadedState: {
      auth: {
        user: null,
        token: null,
        isAuthenticated: false,
        loading: false,
        ...initialState.auth,
      },
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false,
      }).concat(baseApi.middleware),
  })
}

const renderHeader = (initialState = {}) => {
  const store = createTestStore(initialState)
  const persistor = persistStore(store)

  return render(
    <Provider store={store}>
      <PersistGate loading={<div>Loading...</div>} persistor={persistor}>
        <BrowserRouter future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}>
          <ThemeProvider theme={theme}>
            <Header />
          </ThemeProvider>
        </BrowserRouter>
      </PersistGate>
    </Provider>
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